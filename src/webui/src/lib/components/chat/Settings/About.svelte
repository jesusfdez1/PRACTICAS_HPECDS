<script lang="ts">
    	import {WEB_UI_VERSION } from "$lib/constants";
        import {info} from "$lib/stores";
</script>

    <div class=" space-y-3">
        <div>
            <div class=" mb-2.5 text-sm font-medium">Versión de la interfaz web</div>
            <div class="flex w-full">
                <div class="flex-1 text-xs text-gray-700 dark:text-gray-200">
                    {WEB_UI_VERSION}
                </div>
            </div>
        </div>

        <hr class=" dark:border-gray-700" />

        <div>
            <div class=" mb-2.5 text-sm font-medium">Versión de Ollama</div>
            <div class="flex w-full">
                <div class="flex-1 text-xs text-gray-700 dark:text-gray-200">
                    {$info?.ollama.version ?? "N/A"}
                </div>
            </div>
        </div>
    </div>
