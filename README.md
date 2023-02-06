# SerWO Deployment processs

## **User directory structure**
The user directory should look like (see serwo/examples for reference)
```
folder/src - directory containing function code

```


## *AWS Step functions*


### **Deployment commands**

```
Command
    python3 <path..>/aws_create_statemachine.py <path-to-user-dir> <workflow-description-filename> <trigger-type>

NOTE
    trigger types - REST | SQS
```

## *Azure Durable functions*
### **Deployment commands**

```
Command
    python3 <path..>/azure_create_statemachine.py <path-to-user-dir> <workflow-description-filename> <trigger-type>

NOTE
    trigger types - !To be integrated!
```
