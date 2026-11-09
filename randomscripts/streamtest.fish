#!/usr/bin/fish

set -l GPU_BOX_URL "http://100.121.126.7:8080"
set -l MODEL_NAME "qwen"
set -l BEARER_TOKEN "your-super-secret-key"

function run_prefill -a gpu_box_url model_name bearer_token
    jq -n \
        --arg model "$model_name" \
        --arg timestamp (date) \
        --rawfile content /dev/stdin \
        '{
            model: $model,
            messages: [{
                role: "user",
                content: ($content + "\n\nTimestamp: " + $timestamp)
            }],
            stream: true,
            return_progress: true,
            cache_prompt: true,
            max_tokens: 1
        }' |
    curl -sS -N -X POST "$gpu_box_url/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $bearer_token" \
        -d @- |
    while read -l line
        if string match -q 'data: *' -- "$line"
            set -l json (string sub -s 7 -- "$line")

            if test "$json" = "[DONE]"
                break
            end

            echo "$json" | jq -r '
                if .prompt_progress then
                    "⚡ Prefill: \(.prompt_progress.processed)/\(.prompt_progress.total) tokens (\(
                        if .prompt_progress.total > 0 then
                            (.prompt_progress.processed / .prompt_progress.total * 100) | floor
                        else 0 end
                    )%) | Cached: \(.prompt_progress.cache // 0) | Elapsed: \(.prompt_progress.time_ms / 1000)s"
                elif .choices[0].delta.reasoning_content then
                    .choices[0].delta.reasoning_content
                elif .choices[0].delta.content then
                    .choices[0].delta.content
                else
                    empty
                end
            ' 2>/dev/null
        end
    end
end

# --- usage ---
printf '%s\n' '
content/a__old_tui/adapters/__init__.py : 4 lines
content/a__old_tui/adapters/disk_adapter.py : 124 lines
content/a__old_tui/adapters/terminal/linux.py : 92 lines
content/a__old_tui/adapters/terminal/scripted_terminal_adapter.py : 158 lines
content/a__old_tui/adapters/yaml_parser.py : 15 lines
content/a__old_tui/clanker.py : 85 lines
content/a__old_tui/core/__init__.py : 2 lines
content/a__old_tui/core/core/entities.py : 228 lines
content/a__old_tui/core/engine.py : 45 lines
content/a__old_tui/core/engine_deps/__init__.py : 2 lines
content/a__old_tui/core/engine_deps/ports.py : 75 lines
content/a__old_tui/core/engine_deps/result.py : 156 lines
content/a__old_tui/modules/__init__.py : 5 lines
content/a__old_tui/modules/asset_ingestion/__init__.py : 7 lines
content/a__old_tui/modules/asset_ingestion/commons/error_collector.py : 22 lines
content/a__old_tui/modules/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/a__old_tui/modules/asset_ingestion/ingestion_service.py : 66 lines
content/a__old_tui/modules/asset_ingestion/new/service_workers.py : 63 lines
content/a__old_tui/modules/asset_ingestion/validators/file_list_validator.py : 49 lines
content/a__old_tui/modules/asset_ingestion/validators/fileset_validator.py : 37 lines
content/a__old_tui/modules/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/a__old_tui/modules/keyboard/keyboard_service.py : 61 lines
content/a__old_tui/modules/render_pipeline/__init__.py : 1 lines
content/a__old_tui/modules/render_pipeline/content_shaper.py : 46 lines
content/a__old_tui/modules/render_pipeline/render_service.py : 126 lines
content/a__old_tui/modules/tui/__init__.py : 1 lines
content/a__old_tui/modules/tui/renderer.py : 229 lines
content/a__old_tui/modules/tui/tui_service.py : 31 lines
content/a__old_tui/modules/web_frontend/__init__.py : 1 lines
content/a__old_tui/modules/web_frontend/web_frontend_service.py : 238 lines
content/a__old_tui/stdlib.py : 22 lines
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a_lib/templates/README.template : 1 lines
content/a_lib/templates/config.template : 36 lines
content/a_lib/templates/documentation/architecture.template : 1 lines
content/a_lib/templates/documentation/backlog.template : 5 lines
content/a_lib/templates/documentation/north-star.template : 1 lines
content/a_lib/templates/documentation/project-history.template : 1 lines
content/backend/__init__.py : 1 lines
content/backend/adapters/__init__.py : 2 lines
content/backend/adapters/disk_adapter.py : 151 lines
content/backend/adapters/yaml_parser.py : 14 lines
content/backend/asset_ingestion/__init__.py : 7 lines
content/backend/asset_ingestion/commons/error_collector.py : 22 lines
content/backend/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/backend/asset_ingestion/ingestion_service.py : 156 lines
content/backend/asset_ingestion/new/service_workers.py : 63 lines
content/backend/asset_ingestion/validators/file_list_validator.py : 49 lines
content/backend/asset_ingestion/validators/fileset_validator.py : 37 lines
content/backend/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/backend/core/__init__.py : 2 lines
content/backend/core/core/entities.py : 228 lines
content/backend/core/engine_deps/__init__.py : 2 lines
content/backend/core/engine_deps/ports.py : 53 lines
content/backend/core/engine_deps/result.py : 162 lines
content/backend/keyboard/__init__.py : 1 lines
content/backend/keyboard/keyboard_service.py : 61 lines
content/backend/render_pipeline/__init__.py : 2 lines
content/backend/render_pipeline/content_shaper.py : 46 lines
content/backend/render_pipeline/render_service.py : 126 lines
content/backend/server.py : 245 lines
content/backend/stdlib.py : 22 lines
content/clank-server.py : 34 lines
content/web-ui/frontend/api-client.js : 146 lines
content/web-ui/frontend/base-component.js : 17 lines
content/web-ui/frontend/clanker-app.js : 241 lines
content/web-ui/frontend/index.html : 16 lines
content/web-ui/frontend/input-box.js : 75 lines
content/web-ui/frontend/keyboard-bar.js : 180 lines
content/web-ui/frontend/message copy.js : 294 lines
content/web-ui/frontend/message.js : 299 lines
content/web-ui/frontend/messages-box.js : 164 lines
content/web-ui/frontend/sidepanel-left.js : 89 lines
content/web-ui/frontend/sidepanel-right.js : 63 lines
content/web-ui/frontend/toast.js : 23 lines
</pud-manifest>
<shared-manifest>
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a__old_tui/adapters/__init__.py : 4 lines
content/a__old_tui/adapters/disk_adapter.py : 124 lines
content/a__old_tui/adapters/terminal/linux.py : 92 lines
content/a__old_tui/adapters/terminal/scripted_terminal_adapter.py : 158 lines
content/a__old_tui/adapters/yaml_parser.py : 15 lines
content/a__old_tui/clanker.py : 85 lines
content/a__old_tui/core/__init__.py : 2 lines
content/a__old_tui/core/core/entities.py : 228 lines
content/a__old_tui/core/engine.py : 45 lines
content/a__old_tui/core/engine_deps/__init__.py : 2 lines
content/a__old_tui/core/engine_deps/ports.py : 75 lines
content/a__old_tui/core/engine_deps/result.py : 156 lines
content/a__old_tui/modules/__init__.py : 5 lines
content/a__old_tui/modules/asset_ingestion/__init__.py : 7 lines
content/a__old_tui/modules/asset_ingestion/commons/error_collector.py : 22 lines
content/a__old_tui/modules/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/a__old_tui/modules/asset_ingestion/ingestion_service.py : 66 lines
content/a__old_tui/modules/asset_ingestion/new/service_workers.py : 63 lines
content/a__old_tui/modules/asset_ingestion/validators/file_list_validator.py : 49 lines
content/a__old_tui/modules/asset_ingestion/validators/fileset_validator.py : 37 lines
content/a__old_tui/modules/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/a__old_tui/modules/keyboard/keyboard_service.py : 61 lines
content/a__old_tui/modules/render_pipeline/__init__.py : 1 lines
content/a__old_tui/modules/render_pipeline/content_shaper.py : 46 lines
content/a__old_tui/modules/render_pipeline/render_service.py : 126 lines
content/a__old_tui/modules/tui/__init__.py : 1 lines
content/a__old_tui/modules/tui/renderer.py : 229 lines
content/a__old_tui/modules/tui/tui_service.py : 31 lines
content/a__old_tui/modules/web_frontend/__init__.py : 1 lines
content/a__old_tui/modules/web_frontend/web_frontend_service.py : 238 lines
content/a__old_tui/stdlib.py : 22 lines
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a_lib/templates/README.template : 1 lines
content/a_lib/templates/config.template : 36 lines
content/a_lib/templates/documentation/architecture.template : 1 lines
content/a_lib/templates/documentation/backlog.template : 5 lines
content/a_lib/templates/documentation/north-star.template : 1 lines
content/a_lib/templates/documentation/project-history.template : 1 lines
content/backend/__init__.py : 1 lines
content/backend/adapters/__init__.py : 2 lines
content/backend/adapters/disk_adapter.py : 151 lines
content/backend/adapters/yaml_parser.py : 14 lines
content/backend/asset_ingestion/__init__.py : 7 lines
content/backend/asset_ingestion/commons/error_collector.py : 22 lines
content/backend/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/backend/asset_ingestion/ingestion_service.py : 156 lines
content/backend/asset_ingestion/new/service_workers.py : 63 lines
content/backend/asset_ingestion/validators/file_list_validator.py : 49 lines
content/backend/asset_ingestion/validators/fileset_validator.py : 37 lines
content/backend/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/backend/core/__init__.py : 2 lines
content/backend/core/core/entities.py : 228 lines
content/backend/core/engine_deps/__init__.py : 2 lines
content/backend/core/engine_deps/ports.py : 53 lines
content/backend/core/engine_deps/result.py : 162 lines
content/backend/keyboard/__init__.py : 1 lines
content/backend/keyboard/keyboard_service.py : 61 lines
content/backend/render_pipeline/__init__.py : 2 lines
content/backend/render_pipeline/content_shaper.py : 46 lines
content/backend/render_pipeline/render_service.py : 126 lines
content/backend/server.py : 245 lines
content/backend/stdlib.py : 22 lines
content/clank-server.py : 34 lines
content/web-ui/frontend/api-client.js : 146 lines
content/web-ui/frontend/base-component.js : 17 lines
content/web-ui/frontend/clanker-app.js : 241 lines
content/web-ui/frontend/index.html : 16 lines
content/web-ui/frontend/input-box.js : 75 lines
content/web-ui/frontend/keyboard-bar.js : 180 lines
content/web-ui/frontend/message copy.js : 294 lines
content/web-ui/frontend/message.js : 299 lines
content/web-ui/frontend/messages-box.js : 164 lines
content/web-ui/frontend/sidepanel-left.js : 89 lines
content/web-ui/frontend/sidepanel-right.js : 63 lines
content/web-ui/frontend/toast.js : 23 lines
</pud-manifest>
<shared-manifest>
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a__old_tui/adapters/__init__.py : 4 lines
content/a__old_tui/adapters/disk_adapter.py : 124 lines
content/a__old_tui/adapters/terminal/linux.py : 92 lines
content/a__old_tui/adapters/terminal/scripted_terminal_adapter.py : 158 lines
content/a__old_tui/adapters/yaml_parser.py : 15 lines
content/a__old_tui/clanker.py : 85 lines
content/a__old_tui/core/__init__.py : 2 lines
content/a__old_tui/core/core/entities.py : 228 lines
content/a__old_tui/core/engine.py : 45 lines
content/a__old_tui/core/engine_deps/__init__.py : 2 lines
content/a__old_tui/core/engine_deps/ports.py : 75 lines
content/a__old_tui/core/engine_deps/result.py : 156 lines
content/a__old_tui/modules/__init__.py : 5 lines
content/a__old_tui/modules/asset_ingestion/__init__.py : 7 lines
content/a__old_tui/modules/asset_ingestion/commons/error_collector.py : 22 lines
content/a__old_tui/modules/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/a__old_tui/modules/asset_ingestion/ingestion_service.py : 66 lines
content/a__old_tui/modules/asset_ingestion/new/service_workers.py : 63 lines
content/a__old_tui/modules/asset_ingestion/validators/file_list_validator.py : 49 lines
content/a__old_tui/modules/asset_ingestion/validators/fileset_validator.py : 37 lines
content/a__old_tui/modules/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/a__old_tui/modules/keyboard/keyboard_service.py : 61 lines
content/a__old_tui/modules/render_pipeline/__init__.py : 1 lines
content/a__old_tui/modules/render_pipeline/content_shaper.py : 46 lines
content/a__old_tui/modules/render_pipeline/render_service.py : 126 lines
content/a__old_tui/modules/tui/__init__.py : 1 lines
content/a__old_tui/modules/tui/renderer.py : 229 lines
content/a__old_tui/modules/tui/tui_service.py : 31 lines
content/a__old_tui/modules/web_frontend/__init__.py : 1 lines
content/a__old_tui/modules/web_frontend/web_frontend_service.py : 238 lines
content/a__old_tui/stdlib.py : 22 lines
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a_lib/templates/README.template : 1 lines
content/a_lib/templates/config.template : 36 lines
content/a_lib/templates/documentation/architecture.template : 1 lines
content/a_lib/templates/documentation/backlog.template : 5 lines
content/a_lib/templates/documentation/north-star.template : 1 lines
content/a_lib/templates/documentation/project-history.template : 1 lines
content/backend/__init__.py : 1 lines
content/backend/adapters/__init__.py : 2 lines
content/backend/adapters/disk_adapter.py : 151 lines
content/backend/adapters/yaml_parser.py : 14 lines
content/backend/asset_ingestion/__init__.py : 7 lines
content/backend/asset_ingestion/commons/error_collector.py : 22 lines
content/backend/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/backend/asset_ingestion/ingestion_service.py : 156 lines
content/backend/asset_ingestion/new/service_workers.py : 63 lines
content/backend/asset_ingestion/validators/file_list_validator.py : 49 lines
content/backend/asset_ingestion/validators/fileset_validator.py : 37 lines
content/backend/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/backend/core/__init__.py : 2 lines
content/backend/core/core/entities.py : 228 lines
content/backend/core/engine_deps/__init__.py : 2 lines
content/backend/core/engine_deps/ports.py : 53 lines
content/backend/core/engine_deps/result.py : 162 lines
content/backend/keyboard/__init__.py : 1 lines
content/backend/keyboard/keyboard_service.py : 61 lines
content/backend/render_pipeline/__init__.py : 2 lines
content/backend/render_pipeline/content_shaper.py : 46 lines
content/backend/render_pipeline/render_service.py : 126 lines
content/backend/server.py : 245 lines
content/backend/stdlib.py : 22 lines
content/clank-server.py : 34 lines
content/web-ui/frontend/api-client.js : 146 lines
content/web-ui/frontend/base-component.js : 17 lines
content/web-ui/frontend/clanker-app.js : 241 lines
content/web-ui/frontend/index.html : 16 lines
content/web-ui/frontend/input-box.js : 75 lines
content/web-ui/frontend/keyboard-bar.js : 180 lines
content/web-ui/frontend/message copy.js : 294 lines
content/web-ui/frontend/message.js : 299 lines
content/web-ui/frontend/messages-box.js : 164 lines
content/web-ui/frontend/sidepanel-left.js : 89 lines
content/web-ui/frontend/sidepanel-right.js : 63 lines
content/web-ui/frontend/toast.js : 23 lines
</pud-manifest>
<shared-manifest>
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a__old_tui/adapters/__init__.py : 4 lines
content/a__old_tui/adapters/disk_adapter.py : 124 lines
content/a__old_tui/adapters/terminal/linux.py : 92 lines
content/a__old_tui/adapters/terminal/scripted_terminal_adapter.py : 158 lines
content/a__old_tui/adapters/yaml_parser.py : 15 lines
content/a__old_tui/clanker.py : 85 lines
content/a__old_tui/core/__init__.py : 2 lines
content/a__old_tui/core/core/entities.py : 228 lines
content/a__old_tui/core/engine.py : 45 lines
content/a__old_tui/core/engine_deps/__init__.py : 2 lines
content/a__old_tui/core/engine_deps/ports.py : 75 lines
content/a__old_tui/core/engine_deps/result.py : 156 lines
content/a__old_tui/modules/__init__.py : 5 lines
content/a__old_tui/modules/asset_ingestion/__init__.py : 7 lines
content/a__old_tui/modules/asset_ingestion/commons/error_collector.py : 22 lines
content/a__old_tui/modules/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/a__old_tui/modules/asset_ingestion/ingestion_service.py : 66 lines
content/a__old_tui/modules/asset_ingestion/new/service_workers.py : 63 lines
content/a__old_tui/modules/asset_ingestion/validators/file_list_validator.py : 49 lines
content/a__old_tui/modules/asset_ingestion/validators/fileset_validator.py : 37 lines
content/a__old_tui/modules/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/a__old_tui/modules/keyboard/keyboard_service.py : 61 lines
content/a__old_tui/modules/render_pipeline/__init__.py : 1 lines
content/a__old_tui/modules/render_pipeline/content_shaper.py : 46 lines
content/a__old_tui/modules/render_pipeline/render_service.py : 126 lines
content/a__old_tui/modules/tui/__init__.py : 1 lines
content/a__old_tui/modules/tui/renderer.py : 229 lines
content/a__old_tui/modules/tui/tui_service.py : 31 lines
content/a__old_tui/modules/web_frontend/__init__.py : 1 lines
content/a__old_tui/modules/web_frontend/web_frontend_service.py : 238 lines
content/a__old_tui/stdlib.py : 22 lines
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
content/a_lib/templates/README.template : 1 lines
content/a_lib/templates/config.template : 36 lines
content/a_lib/templates/documentation/architecture.template : 1 lines
content/a_lib/templates/documentation/backlog.template : 5 lines
content/a_lib/templates/documentation/north-star.template : 1 lines
content/a_lib/templates/documentation/project-history.template : 1 lines
content/backend/__init__.py : 1 lines
content/backend/adapters/__init__.py : 2 lines
content/backend/adapters/disk_adapter.py : 151 lines
content/backend/adapters/yaml_parser.py : 14 lines
content/backend/asset_ingestion/__init__.py : 7 lines
content/backend/asset_ingestion/commons/error_collector.py : 22 lines
content/backend/asset_ingestion/extractors/map_extractor2.py : 270 lines
content/backend/asset_ingestion/ingestion_service.py : 156 lines
content/backend/asset_ingestion/new/service_workers.py : 63 lines
content/backend/asset_ingestion/validators/file_list_validator.py : 49 lines
content/backend/asset_ingestion/validators/fileset_validator.py : 37 lines
content/backend/asset_ingestion/validators/overflow_validator2.py : 39 lines
content/backend/core/__init__.py : 2 lines
content/backend/core/core/entities.py : 228 lines
content/backend/core/engine_deps/__init__.py : 2 lines
content/backend/core/engine_deps/ports.py : 53 lines
content/backend/core/engine_deps/result.py : 162 lines
content/backend/keyboard/__init__.py : 1 lines
content/backend/keyboard/keyboard_service.py : 61 lines
content/backend/render_pipeline/__init__.py : 2 lines
content/backend/render_pipeline/content_shaper.py : 46 lines
content/backend/render_pipeline/render_service.py : 126 lines
content/backend/server.py : 245 lines
content/backend/stdlib.py : 22 lines
content/clank-server.py : 34 lines
content/web-ui/frontend/api-client.js : 146 lines
content/web-ui/frontend/base-component.js : 17 lines
content/web-ui/frontend/clanker-app.js : 241 lines
content/web-ui/frontend/index.html : 16 lines
content/web-ui/frontend/input-box.js : 75 lines
content/web-ui/frontend/keyboard-bar.js : 180 lines
content/web-ui/frontend/message copy.js : 294 lines
content/web-ui/frontend/message.js : 299 lines
content/web-ui/frontend/messages-box.js : 164 lines
content/web-ui/frontend/sidepanel-left.js : 89 lines
content/web-ui/frontend/sidepanel-right.js : 63 lines
content/web-ui/frontend/toast.js : 23 lines
</pud-manifest>
<shared-manifest>
content/a_lib/shared-assets/config-fragments/shared_cfg.yaml : 92 lines
content/a_lib/shared-assets/config-fragments/system_cfg.yaml : 4 lines
content/a_lib/shared-assets/layouts/btn_active.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_hl.layout : 6 lines
content/a_lib/shared-assets/layouts/btn_inactive.layout : 6 lines
content/a_lib/shared-assets/layouts/prompt.layout : 4 lines
content/a_lib/shared-assets/layouts/ui.layout : 22 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/config-development.mode_instruction : 2 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/do-mode.mode_instruction : 7 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/doc-management-mode.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/north-star-mode.mode_instruction : 4 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/plan-mode.mode_instruction : 6 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_content.mode_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/behavioural_instructions/readme_structure.mode_instruction : 3 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/config-style.doctrine : 7 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme.structure_spec : 48 lines
content/a_lib/shared-assets/prompt-fragments/doctrines/readme_messaging.intent : 17 lines
content/a_lib/shared-assets/prompt-fragments/general-rules.md : 2 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/debloat-instructions.md : 29 lines
content/a_lib/shared-assets/prompt-fragments/lost_and_found/domain-debloat.md : 4 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/backlog-output-instructions.output_instruction : 11 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/code-output-instruction.output_instruction : 44 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/config-dev-output.output_instruction : 1 lines
content/a_lib/shared-assets/prompt-fragments/output-instructions/history-output-instructions.output_instruction : 12 lines
' | run_prefill "$GPU_BOX_URL" "$MODEL_NAME" "$BEARER_TOKEN"
