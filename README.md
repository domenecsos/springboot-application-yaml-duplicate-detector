# Spring Boot application.yaml duplicate keys detector

## What this script does

This Python script scans all folders in current directory searching application.yml/yaml files. 

When found, it will compare the application file to other application-*.yml/yaml files of specific Spring profiles.

If given a parameter, the script will use it as the starting folder.

## How to run it in a Docker container

### Linux/Unix/Mac shell

All folders from here:
```
docker run --rm -v $PWD:/app -w /app python:3.12-slim sh -c "pip install pyyaml >/dev/null && python /app/spring_yaml_sanity.py user-service"
```
One "user-service" folders from here
```
docker run --rm -v "$PWD":/app -w /app python:3.12-slim sh -c "pip install pyyaml >/dev/null && python /app/spring_yaml_sanity.py user-service"
```

### Windows
All folders from here
```
docker run --rm -v "%CD%":/app -w /app python:3.12-slim sh -c "pip install pyyaml >/dev/null && python /app/spring_yaml_sanity.py user-service"
```
One "user-service" folders from here
```
docker run --rm -v "%CD%":/app -w /app python:3.12-slim sh -c "pip install pyyaml >/dev/null && python /app/spring_yaml_sanity.py user-service"
```

### Sample output

```
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

[notice] A new release of pip is available: 25.0.1 -> 25.3
[notice] To update, run: pip install --upgrade pip

Folder: /app/user-service/src/main/resources
Base:   /app/user-service/src/main/resources/application.yml
ERROR: /app/user-service/src/main/resources/application-aws.yml: key 'external.advice-service.base-url' duplicates base value '${EXTERNAL_ADVICE_SERVICE_BASE_URL}'
ERROR: /app/user-service/src/main/resources/application-aws.yml: key 'external.assignment-service.base-url' duplicates base value '${EXTERNAL_ASSIGNMENT_SERVICE_BASE_URL}'
ERROR: /app/user-service/src/main/resources/application-aws.yml: key 'spring.jpa.show-sql' duplicates base value '${JPA_SHOW_SQL:true}'
ERROR: /app/user-service/src/main/resources/application-docker.yml: key 'aws.accessKey' duplicates base value '${AWS_ACCESS_KEY}'
ERROR: /app/user-service/src/main/resources/application-docker.yml: key 'aws.region' duplicates base value '${AWS_REGION}'
ERROR: /app/user-service/src/main/resources/application-docker.yml: key 'aws.s3.bucket' duplicates base value '${AWS_S3_BUCKET}'
ERROR: /app/user-service/src/main/resources/application-docker.yml: key 'spring.kafka.topics.activity-log.created' duplicates base value '${KAFKA_TOPIC_ACTIVITY_LOG_CREATED}'
```
