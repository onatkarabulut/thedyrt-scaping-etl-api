#!/usr/bin/env bash
# run-all.sh

# her alt dizinde docker-compose.yml var ise, up komutunu arka planda çalıştır
find . -type f -name docker-compose.yml -printf '%h\n' \
  | while read dir; do
      (
        cd "$dir"
        echo "⬢ Starting compose in $dir"
        docker-compose up
      ) &
    done

# tüm arka plan işlerinin bitmesini bekle
wait
echo "✅ All composed!"
