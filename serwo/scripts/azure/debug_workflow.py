import argparse
import time
import json
import urllib.request
import sys
from datetime import datetime

def get_status(uri, show_history=True):
    try:
        if show_history:
            if '?' in uri:
                uri += "&showHistory=true&showInput=true&showOutput=true"
            else:
                uri += "?showHistory=true&showInput=true&showOutput=true"
        
        req = urllib.request.Request(uri)
        with urllib.request.urlopen(req) as response:
            if response.status == 202: # Accepted (Running)
                return json.loads(response.read().decode())
            elif response.status == 200: # OK (Completed/Failed etc)
                return json.loads(response.read().decode())
            else:
                print(f"Unexpected status code: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching status: {e}")
        return None

def format_timestamp(ts):
    if not ts: return ""
    return ts.replace('T', ' ').split('.')[0] # Simple formatting

def print_history(history):
    print(f"{'Timestamp':<25} | {'EventType':<20} | {'Name':<30} | {'Status/Details'}")
    print("-" * 100)
    for event in history:
        ts = format_timestamp(event.get('Timestamp', ''))
        event_type = event.get('EventType')
        name = event.get('Name', '')
        
        details = ""
        if event_type == 'ExecutionStarted':
            details = f"Input: {str(event.get('Input'))[:50]}..."
        elif event_type == 'TaskScheduled':
            details = f"Scheduled: {name}"
        elif event_type == 'TaskCompleted':
            details = f"Result: {str(event.get('Result'))[:50]}..."
        elif event_type == 'TaskFailed':
            details = f"Reason: {event.get('Reason')}"
        elif event_type == 'ExecutionCompleted':
            details = f"Status: {event.get('OrchestrationStatus')}"
        
        if not name and event_type == 'ExecutionStarted':
             name = "Orchestrator"

        print(f"{ts:<25} | {event_type:<20} | {name:<30} | {details}")

def monitor_workflow(uri):
    print(f"Monitoring workflow: {uri}")
    print("Waiting for updates...")
    
    last_status = None
    running = True
    
    while running:
        status_data = get_status(uri)
        if not status_data:
            time.sleep(2)
            continue
            
        runtime_status = status_data.get('runtimeStatus')
        history = status_data.get('historyEvents', [])
        
        # Clear screen/move up (simple implementation: just print separator)
        print("\n" + "="*80)
        print(f"Current Status: {runtime_status}")
        print("="*80)
        
        print_history(history)
        
        if runtime_status in ['Completed', 'Failed', 'Terminated', 'Canceled']:
            running = False
            print(f"\nWorkflow finished with status: {runtime_status}")
            if runtime_status == 'Failed':
                print(f"Failure Output: {status_data.get('output')}")
            else:
                 print(f"Output: {status_data.get('output')}")
        else:
            time.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Trace Azure Durable Functions execution.')
    parser.add_argument('uri', help='The statusQueryGetUri from the orchestration start response')
    
    args = parser.parse_args()
    
    # Extract app name from URI
    # URI format: https://<appname>.azurewebsites.net/...
    try:
        if '://' in args.uri:
            app_name = args.uri.split('://')[1].split('.')[0]
            print(f"\n[INFO] To see real-time console logs (print statements), run in another terminal:")
            print(f"       func azure functionapp logstream {app_name}\n")
    except:
        pass

    monitor_workflow(args.uri)
