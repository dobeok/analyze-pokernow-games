# extract flops from raw log files

mkdir -p ../data/processed/flop
for FILE in ../data/raw/*.csv;
    do echo "$FILE";
    basename=$(basename "${FILE%.*}")
    # echo "$basename"
    grep -i 'flop' "$FILE" > "../data/processed/flop/flop_$basename.csv";
done