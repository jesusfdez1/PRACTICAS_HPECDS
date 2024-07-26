<script lang="ts">
    	import {WEB_UI_VERSION } from "$lib/constants";
        import {info} from "$lib/stores";
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm mb-6">
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

        <hr class=" dark:border-gray-700" />

        <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
            Creado por <a
                class=" text-gray-500 dark:text-gray-300 font-medium"
                href="https://github.com/tjbck"
                target="_blank">Timothy J. Baek</a
            >
        </div>
        <div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
            Modificado por <a
            class=" text-gray-500 dark:text-gray-300 font-medium"
            href="https://github.com/jesusfdez1"
            target="_blank">Jesús Fernández López</a
        >
        </div>
    </div>
</div>