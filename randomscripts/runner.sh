#!/bin/bash

PORT=8080
API_KEY="your-super-secret-key"
DISPLAY_SERVICE="plasmalogin"

MODEL_FILES=(
    "Qwen3.8-27B-GSQ-RCO-IQ2_XS-mtp.gguf"
    "Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf"
    "Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf"
)

MODEL_ARGS_LIST=(
"
    -m Qwen3.8-27B-GSQ-RCO-IQ2_XS-mtp.gguf 
    -c 35000
    --spec-type draft-mtp 
    --spec-draft-n-max 1
"
"   
    -m Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf 
    -c 50000
    --spec-type draft-mtp 
    --spec-draft-n-max 1
"
"   
    -m Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf
    -c 10000 
    --spec-type draft-mtp 
    --spec-draft-n-max 1
"
)

STATIC_ARGS=(
    -fa on
    --parallel 1
    -ngl 999
    -ctk q4_0
    -ctv q4_0
    --jinja
    -lv 3
    --no-mmproj
    --host 0.0.0.0
    --port "$PORT"
    --api-key "$API_KEY"
)

usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  stop                 Stop the login manager"
    echo "  start                Start the login manager"
    echo "  run                  List available models"
    echo "  run <number>         Run a model by number"
    exit 1
}

case "$1" in
    stop)
        echo "[+] Stopping $DISPLAY_SERVICE..."
        sudo systemctl stop "$DISPLAY_SERVICE"
        echo "[+] Done."
        ;;
        
    start)
        echo "[+] Starting $DISPLAY_SERVICE..."
        sudo systemctl start "$DISPLAY_SERVICE"
        echo "[+] Done."
        ;;
        
    run)
        shift
        if [ -z "$1" ]; then
            echo "=========================================="
            echo "          Available Models                "
            echo "=========================================="
            for i in "${!MODEL_FILES[@]}"; do
                num=$((i + 1))
                echo "  $num: ${MODEL_FILES[$i]}"
            done
            echo ""
            echo "Usage: $0 run <number>"
            exit 0
        fi
        
        INPUT="$1"
        
        if [[ "$INPUT" =~ ^[0-9]+$ ]]; then
            index=$((INPUT - 1))
            if [ "$index" -ge 0 ] && [ "$index" -lt "${#MODEL_FILES[@]}" ]; then
                read -r -a RUN_ARGS <<< "$(xargs <<< "${MODEL_ARGS_LIST[$index]}")"
                
                echo "[+] Launching llama-server with model: ${MODEL_FILES[$index]}"
                echo "------------------------------------------"
                exec llama-server "${RUN_ARGS[@]}" "${STATIC_ARGS[@]}"
            fi
        fi
        
        echo "[-] Error: Invalid selection '$INPUT'."
        echo "Run '$0 run' to see available models."
        exit 1
        ;;
        
    *)
        usage
        ;;
esac
