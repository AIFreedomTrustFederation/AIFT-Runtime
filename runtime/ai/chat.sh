#!/data/data/com.termux/files/usr/bin/bash

while true
do
echo
read -p "You > " INPUT

curl -s http://127.0.0.1:8080/v1/chat/completions \
-H "Content-Type: application/json" \
-d "{
\"messages\":[
{
\"role\":\"system\",
\"content\":\"You are Aetherion, the local sovereign AI operating system assistant.\"
},
{
\"role\":\"user\",
\"content\":\"$INPUT\"
}
]
}" | grep -o '\"content\":\"[^\"]*' | sed 's/\"content\":\"//'

done
