<script lang="ts">
	import { API_MICROSERVICES_PORT, API_MICROSERVICES_BASE_URL } from "$lib/constants";
	import toast from "svelte-french-toast";
	let dateInputs: { start: string, end: string }[] = [];
	let startDate = '';
	let endDate = '';
	
	function addDateInput() {
	  if (startDate === '') {
		toast.error('Ingresa como mínimo una fecha de inicio');
		return;
	  }

	  if (endDate < startDate && endDate !== '') {
		toast.error('La fecha de fin debe ser mayor o igual a la fecha de inicio');
		return;
	  }
	
	  dateInputs = [...dateInputs, { start: startDate, end: endDate }];
	  startDate = '';
	  endDate = '';
	}
	
	function removeDateInput(index: number) {
	  dateInputs.splice(index, 1);
	  dateInputs = [...dateInputs];
	}
	
	async function handleSubmit() {
	  if (dateInputs.length === 0) {
		toast.error('Ingresa al menos una fecha');
		return;
	  }
	
	  const data = {
		dates: dateInputs
	  };
	  
	  try {
		const response = await fetch(API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT + '/downloader', {
		  method: 'POST',
		  headers: { 'Content-Type': 'application/json' },
		  body: JSON.stringify(data)
		});
	

            if (response.ok) {
                console.log('Archivos descargados correctamente.');
				toast.success('Archivos descargados correctamente');
            } else {
                console.error('Error al enviar fecha(s) al servidor.');
				toast.error('Error al enviar fecha(s) al servidor');
            }
        } catch (error) {
            console.error('Error en la solicitud:', error);
			toast.error('Error en la solicitud');
        }
	
	  // Limpiar los inputs después de manejar la respuesta
	  dateInputs = [];
	  startDate = '';
	  endDate = '';
	}
  </script>
  
    <div class="py-0.0"> <!-- No hay necesidad de espacio adicional aquí -->
	<div class="text-xs font-medium">Seleccionar fecha(s):</div>
	<div class="flex space-x-2 mt-2">
		<label for="end-date" class="text-xs font-medium">Fecha de inicio</label>

	  <input
		type="date"
		bind:value={startDate}
		max={new Date().toISOString().split('T')[0]} 
		class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
	  />
	  <label for="end-date" class="text-xs font-medium">Fecha de fin</label>

	  <input
		type="date"
		bind:value={endDate}
		max={new Date().toISOString().split('T')[0]} 
		class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
	  />
	  <button class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded ml-2" on:click={addDateInput}>+</button>
	</div>
  </div>
  
  <!-- Mostrar las fechas ingresadas -->
  {#if dateInputs.length > 0}
	<div class="py-0.5">
	  <hr class=" dark:border-gray-700" />
	  
	  <div class="text-xs font-medium mt-4 mb-4"><strong>Fechas seleccionadas:</strong></div>
	  {#each dateInputs as dateInput, index}
		<div class="flex items-center space-x-2 mt-2">
			<button class="text-white-500 hover:text-white-600 bg-red-500 hover:bg-red-600 text-white py-1 px-2.5 rounded" on:click={(event) => removeDateInput(index)}>
				<div class="flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
					</svg>
				</div>
			</button>			
			{#if dateInput.start && dateInput.end}
			<span>{new Date(dateInput.start).toLocaleDateString('es-ES')} - {new Date(dateInput.end).toLocaleDateString('es-ES')}</span>
		  {:else if dateInput.start}
			<span>{new Date(dateInput.start).toLocaleDateString('es-ES')}</span>
			{:else if dateInput.end}
			<span>{new Date(dateInput.end).toLocaleDateString('es-ES')}</span>
		  {/if}
		</div>
	  {/each}
	</div>
	<div class="py-0.5 flex justify-end">
		<button class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded" on:click={handleSubmit}>
		  Enviar
		</button>
	  </div>
	  
  {/if}
  
  <style>
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		/* display: none; <- Crashes Chrome on hover */
		-webkit-appearance: none;
		margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
	}
</style>