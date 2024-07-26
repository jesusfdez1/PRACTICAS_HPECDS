<script lang="ts">
    import { onMount } from 'svelte';
    import { API_MICROSERVICES_PORT, API_MICROSERVICES_BASE_URL } from "$lib/constants";

    let importFileInputElement: HTMLInputElement;
    let importedFiles: { id: number, name: string }[] = [];
    let nextFileId = 1;
    let importFiles: File[] = []; // Cambia a un array estándar de File
    
    function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    importFiles = input.files ? Array.from(input.files) : [];

    // Actualizar la lista de nombres de archivos importados
    updateFileNames();
}

async function handleSubmit() {
    if (importFiles && importFiles.length > 0) {
        const formData = new FormData();
        importFiles.forEach(file => {
            formData.append('files[]', file);
        });

        try {
            const response = await fetch(API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT + '/importer', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                console.log('Archivos subidos correctamente.');
                window.alert('Archivos subidos correctamente.');
                // Limpiar la lista después de la subida exitosa si es necesario
                importedFiles = [];
                importFiles = [];
            } else {
                console.error('Error al subir archivos al servidor.');
                window.alert('Error al subir archivos al servidor.');
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
            window.alert('Error en la solicitud.');
        }
    } else {
        window.alert('Debe seleccionar al menos un archivo para enviar.');
    }
}


    function updateFileNames() {
        const newFiles: { id: number, name: string }[] = [];

        if (importFiles && importFiles.length > 0) {
            for (let i = 0; i < importFiles.length; i++) {
                const file = importFiles[i];
                if (file.type === 'application/pdf') {
                    newFiles.push({ id: nextFileId++, name: file.name });
                } else {
                    console.log(`El archivo ${file.name} no es un PDF.`);
                }
            }
        }

        importedFiles = newFiles;
    }

    function removeFile(idToRemove: number) {
    // Eliminar el archivo de importedFiles
    importedFiles = importedFiles.filter(file => file.id !== idToRemove);
    // Actualizar importFiles para reflejar solo los archivos que aún están presentes en importedFiles
    importFiles = importFiles.filter(file => importedFiles.some(f => f.name === file.name));
}

</script>

<div class="flex flex-col">
    <div class="flex">
        <input bind:this={importFileInputElement} type="file" accept=".pdf" multiple hidden 
               on:change={handleFileChange}/>
        <button class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition bg-gray-200 dark:bg-gray-700 s--7fsHGLC475o"
                on:click={() => importFileInputElement.click()}>
            <div class="self-center mr-3">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                     stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round"
                          d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
                </svg>
            </div>
            <div class="self-center">Importar documento(s)</div>
        </button>
    </div>

<!-- Lista de nombres de archivos importados -->
<div class="mt-4">
    {#if importedFiles.length > 0}
        <h2 class="text-sm font-medium">Archivos importados</h2>
        <ul class="grid grid-cols-1 gap-2">
            {#each importedFiles as file}
                <li class="flex items-center bg-transparent py-1 px-2 rounded-lg border border-transparent">
                    <button class="text-white-500 hover:text-white-600 bg-red-500 hover:bg-red-600 text-white py-1 px-2.5 rounded" 
                            on:click={() => removeFile(file.id)}>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                    </button>
                    
                    <span class="ml-1 flex-grow truncate">{file.name}</span>
                </li>
            {/each}
        </ul>

    {/if}
</div>

	<div class="py-0.5 flex justify-end">
        {#if importedFiles.length > 0}
        <button class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded" on:click={handleSubmit} disabled={importedFiles.length === 0}>
             Enviar
            </button>
        {/if}
	  </div>

</div>

<style>
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		/* display: none; <- Crashes Chrome on hover */
		-webkit-appearance: none;
		margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
	}
</style>