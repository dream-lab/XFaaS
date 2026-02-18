import boto3
import sys
import argparse
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_last_invocation_time(stack_info, region):
    """
    Attempts to find the last invocation time by looking at CloudWatch Logs
    for Lambda functions associated with the stack.
    """
    stack_name = stack_info['StackName']
    try:
        # Create new clients for each thread/call to be safe
        cf = boto3.client('cloudformation', region_name=region)
        logs = boto3.client('logs', region_name=region)
        
        # Get stack resources to find Lambda functions
        resources = cf.list_stack_resources(StackName=stack_name)
        
        last_invoked = None
        
        for r in resources.get('StackResources', []):
            if r['ResourceType'] == 'AWS::Lambda::Function':
                func_name = r['PhysicalResourceId']
                log_group_name = f"/aws/lambda/{func_name}"
                
                try:
                    # Get the most recent log stream
                    streams = logs.describe_log_streams(
                        logGroupName=log_group_name,
                        orderBy='LastEventTime',
                        descending=True,
                        limit=1
                    )
                    
                    if streams.get('logStreams'):
                        # lastEventTimestamp is in milliseconds
                        ts = streams['logStreams'][0].get('lastEventTimestamp')
                        if ts:
                            dt = datetime.fromtimestamp(ts / 1000.0, timezone.utc)
                            if last_invoked is None or dt > last_invoked:
                                last_invoked = dt
                except Exception:
                    # Log group might not exist if never invoked
                    pass
                    
        return stack_name, last_invoked

    except Exception as e:
        # print(f"Error checking invocation for {stack_name}: {e}")
        return stack_name, None

def cleanup_stacks(region='ap-south-1', apply=False, target_broken=False, target_stale=False, target_recent=False, delete_all=False):
    """
    Deletes CloudFormation stacks starting with 'XFaaSApp-' based on filtering criteria.
    """
    cf = boto3.client('cloudformation', region_name=region)
    
    print(f"Listing stacks in region {region}...")
    
    try:
        paginator = cf.get_paginator('list_stacks')
        
        stacks = []
        for page in paginator.paginate():
            for stack in page.get('StackSummaries', []):
                if stack['StackStatus'] == 'DELETE_COMPLETE':
                    continue
                if stack['StackName'].startswith('XFaaSApp-'):
                    stacks.append(stack)

        print(f"Found {len(stacks)} stacks matching prefix 'XFaaSApp-'.")
        
        now = datetime.now(timezone.utc)
        
        # Parallelize the check for last invocation
        print("Checking last invocation times (in parallel)...")
        invocation_times = {}
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_last_invocation_time, stack, region) for stack in stacks]
            
            for i, future in enumerate(as_completed(futures)):
                if i % 50 == 0:
                    print(f"Processed {i}/{len(stacks)} stacks...")
                stack_name, last_invoked = future.result()
                invocation_times[stack_name] = last_invoked

        broken_stacks = []
        stale_stacks = []
        recent_stacks = []
        
        for stack in stacks:
            is_broken = 'FAILED' in stack['StackStatus'] or 'ROLLBACK_COMPLETE' in stack['StackStatus']
            
            last_invoked = invocation_times.get(stack['StackName'])
            
            # Fallback to creation/update time if no logs found
            ref_time = last_invoked if last_invoked else stack.get('LastUpdatedTime', stack['CreationTime'])
            
            # Ensure ref_time is timezone-aware (UTC)
            if ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)
                
            age = now - ref_time
            
            # Stale if older than 60 days based on LAST INVOCATION (or creation if never invoked)
            is_stale = age > timedelta(days=60)
            
            stack_info = {
                'name': stack['StackName'],
                'status': stack['StackStatus'],
                'time': ref_time,
                'age_str': f"{age.days} days",
                'last_invoked': "Logs" if last_invoked else "Creation/Update"
            }
            
            if is_broken:
                broken_stacks.append(stack_info)
            elif is_stale:
                stale_stacks.append(stack_info)
            else:
                recent_stacks.append(stack_info)

        # Determine what to delete
        to_delete = []
        
        if delete_all:
             to_delete.extend(broken_stacks)
             to_delete.extend(stale_stacks)
             to_delete.extend(recent_stacks)
        else:
            if target_broken:
                to_delete.extend(broken_stacks)
            if target_stale:
                to_delete.extend(stale_stacks)
            if target_recent:
                to_delete.extend(recent_stacks)

        # Print Listing
        print("\n--- Summary ---")
        print(f"Broken (Failed/Rollback): {len(broken_stacks)}")
        for s in broken_stacks:
            print(f"  [BROKEN] {s['name']} ({s['status']}, Age: {s['age_str']}, Ref: {s['last_invoked']})")
            
        print(f"Stale (>30 days since last invoke): {len(stale_stacks)}")
        for s in stale_stacks:
            print(f"  [STALE]  {s['name']} ({s['status']}, Age: {s['age_str']}, Ref: {s['last_invoked']})")
            
        print(f"Recent (<30 days): {len(recent_stacks)}")
        for s in recent_stacks:
            print(f"  [RECENT] {s['name']} ({s['status']}, Age: {s['age_str']}, Ref: {s['last_invoked']})")

        print("----------------")

        if not to_delete:
            print("\nNo stacks selected for deletion.")
            print("Use --broken, --stale (>30 days), --recent, or --all to select targets.")
            print("Use --apply to execute deletion.")
            return

        print(f"\n[ACTION] Selected {len(to_delete)} stacks for deletion.")
        if not apply:
            print("This is a DRY RUN. Run with --apply to delete.")
            return

        print("\nDeleting...")
        import time
        from botocore.exceptions import ClientError

        for s in to_delete:
            print(f"Deleting stack: {s['name']}")
            retries = 0
            max_retries = 5
            while retries < max_retries:
                try:
                    cf.delete_stack(StackName=s['name'])
                    # Sleep to avoid hitting rate limits (allowed ~10/sec, but safe side 2/sec)
                    time.sleep(0.5) 
                    break
                except ClientError as e:
                    if e.response['Error']['Code'] == 'Throttling':
                        wait = (2 ** retries) * 1
                        print(f"  Throttled. Retrying in {wait}s...")
                        time.sleep(wait)
                        retries += 1
                    else:
                        print(f"Error deleting {s['name']}: {e}")
                        break
                except Exception as e:
                    print(f"Error deleting {s['name']}: {e}")
                    break
            else:
                print(f"Failed to delete {s['name']} after {max_retries} retries.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cleanup XFaaS CloudFormation Stacks')
    parser.add_argument('--region', default='ap-south-1', help='AWS Region')
    parser.add_argument('--apply', action='store_true', help='Perform deletion')
    parser.add_argument('--broken', action='store_true', help='Target broken stacks')
    parser.add_argument('--stale', action='store_true', help='Target stale (>30 days) stacks')
    parser.add_argument('--recent', action='store_true', help='Target recent (<30 days) stacks')
    parser.add_argument('--all', action='store_true', help='Target ALL stacks')

    args = parser.parse_args()
    
    cleanup_stacks(region=args.region, apply=args.apply, target_broken=args.broken, target_stale=args.stale, target_recent=args.recent, delete_all=args.all)
