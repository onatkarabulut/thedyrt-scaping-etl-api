
```bash
$ python extract.py [OPTIONS]
```

| Flag               | Description                                                        | Default                             |
| ------------------ | ------------------------------------------------------------------ | ----------------------------------- |
| `--state STATE`    | Only extract a single state (e.g. `California`).                   | *none* (you must pick at least one) |
| `--all`            | Extract *every* U.S. state in our list.                            | off                                 |
| `--page-size SIZE` | Number of items per request page.                                  | `1000`                              |
| `--brokers HOSTS`  | Comma-separated Kafka `bootstrap.servers` (e.g. `localhost:9092`). | `localhost:9092`                    |
| `--topic TOPIC`    | Kafka topic to produce raw messages into.                          | `campground-raw`                    |
| `--no-kafka`       | Don’t stream into Kafka—just run extraction and return the list.   | off                                 |
| `--help`           | Show this help message.                                            | —                                   |

---

## Example

```bash
python extract.py --state Texas \
    --brokers kafka1:9092,kafka2:9092 \
    --topic raw-camps
```
```bash
python extract.py --all --no-kafka
```
After running, detailed logs will live in:
logs/kafka_logs/extract.log


❯ datamodel-codegen \
  --url https://thedyrt.com/api/v6/campgrounds/ \   
  --input-file-type json \
  --output src/models/campground_full.py \
  --use-standard-collections \
  --use-generic-container-types \
  --snake-case-field
