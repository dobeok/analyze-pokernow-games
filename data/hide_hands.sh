# put this in the same folder as raw log file
# run to remove entries containing hand information

mkdir -p raw
for FILE in *.csv;
    do grep -v -i 'your hand is' "$FILE" > "raw/$FILE";
done