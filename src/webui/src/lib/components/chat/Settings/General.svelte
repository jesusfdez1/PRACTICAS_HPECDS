<script lang="ts">
    let theme = "dark";

    const toggleTheme = async () => {
        if (theme === "dark") {
            theme = "light";
        } else {
            theme = "dark";
        }

        localStorage.theme = theme;

        document.documentElement.classList.remove(theme === "dark" ? "light" : "dark");
        document.documentElement.classList.add(theme);
    };

    // Función para enviar a la API con las longitudes establecidas por el usuario
    const sendToAPI = async () => {
        const chunkLengthElement = document.getElementById('chunkLength');
        const chunkLength = chunkLengthElement ? parseInt((chunkLengthElement as HTMLInputElement).value) : 0;
        const contextLength = parseInt((document.getElementById('contextLength') as HTMLInputElement)?.value);


        // Aquí debes implementar la lógica para enviar a la API con chunkLength y contextLength
        // Por ejemplo:
        const data = {
            chunkLength: chunkLength,
            contextLength: contextLength
        };

        // Ejemplo de cómo podrías enviar los datos a la API usando fetch
        try {
            const response = await fetch('url_de_tu_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                throw new Error('Error al enviar datos a la API');
            }

            const responseData = await response.json();
            console.log('Respuesta de la API:', responseData);
        } catch (error) {
            console.error('Error:', error);
        }
    };
</script>

<div class="flex flex-col space-y-3">
    <div class="text-sm font-medium">Ajustes de la interfaz</div>

    <div>
        <div class="py-0.5 flex w-full justify-between">
            <div class="self-center text-xs font-medium">Temas</div>

            <button
                class="p-1 px-3 text-xs flex rounded transition"
                on:click={() => {
                    toggleTheme();
                }}
            >
                {#if theme === "dark"}
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
                        <path fill-rule="evenodd" d="M7.455 2.004a.75.75 0 01.26.77 7 7 0 009.958 7.967.75.75 0 011.067.853A8.5 8.5 0 116.647 1.921a.75.75 0 01.808.083z" clip-rule="evenodd"/>
                    </svg>
                    <span class="ml-2 self-center"> Oscuro </span>
                {:else}
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 self-center">
                        <path d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.061 1.06l1.06 1.06z"/>
                    </svg>
                    <span class="ml-2 self-center"> Claro </span>
                {/if}
            </button>
        </div>
    </div>
	<hr class=" dark:border-gray-700" />

    <div class="text-sm font-medium">Ajustes del procesamiento de documentos</div>

    <!-- Campos para la longitud de chunking y de contexto -->
    <div class="flex justify-between items-center">
        <label for="chunkLength" class="text-xs font-medium">Longitud de chunking:</label>
        <input type="number" id="chunkLength" min="1" step="1" value="700" class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600">
    </div>

    <div class="flex justify-between items-center">
        <label for="contextLength" class="text-xs font-medium">Longitud de contexto:</label>
        <input type="number" id="contextLength" min="1" step="1" value="200" class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600">
    </div>

	<div class="py-0.5 flex justify-end">
		<button class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"   on:click={() => sendToAPI()}
			>
		  Enviar
		</button>
	  </div>
</div>
