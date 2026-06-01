<script lang="ts">
	let theme = "dark";
	import { API_MICROSERVICES_PORT, API_MICROSERVICES_BASE_URL } from "$lib/constants";
	import { chunks } from "$lib/stores";
	import toast from "svelte-french-toast";

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

	const deleteInfo = async () => {
		try {
			const response = await fetch(API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT + "/clean", {
				method: "DELETE",
				headers: {
					"Content-Type": "application/json"
				}
			});

			if (!response.ok) {
				toast.error("Error al borrar la base de datos");
			} else {
				toast.success("Base de datos borrada correctamente");
			}

			const responseData = await response.json();
			console.log("Respuesta de la API:", responseData);
		} catch (error) {
			console.error("Error:", error);
		}
	};
	// Función para enviar a la API con las longitudes establecidas por el usuario
	const sendToAPI = async () => {
		const chunkLengthElement = document.getElementById("chunkLength");
		const chunkLength = chunkLengthElement
			? parseInt((chunkLengthElement as HTMLInputElement).value)
			: 0;
		const contextLength = parseInt(
			(document.getElementById("contextLength") as HTMLInputElement)?.value
		);

		const data = {
			chunkLength: chunkLength,
			contextLength: contextLength
		};

		try {
			const response = await fetch(
				API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT + "/settings",
				{
					method: "POST",
					headers: {
						"Content-Type": "application/json"
					},
					body: JSON.stringify(data)
				}
			);

			if (!response.ok) {
				toast.error("Error al enviar los datos a la API");
			} else {
				toast.success("Datos enviados correctamente");
			}
		} catch (error) {
			console.error("Error:", error);
			toast.error("Error en la solicitud");
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
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M7.455 2.004a.75.75 0 01.26.77 7 7 0 009.958 7.967.75.75 0 011.067.853A8.5 8.5 0 116.647 1.921a.75.75 0 01.808.083z"
							clip-rule="evenodd"
						/>
					</svg>
					<span class="ml-2 self-center"> Oscuro </span>
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4 self-center"
					>
						<path
							d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.061 1.06l1.06 1.06z"
						/>
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
		<input
			type="number"
			id="chunkLength"
			min="1"
			step="1"
			value={$chunks.chunkLength}
			class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
		/>
	</div>

	<div class="flex justify-between items-center">
		<label for="contextLength" class="text-xs font-medium">Longitud de contexto:</label>
		<input
			type="number"
			id="contextLength"
			min="1"
			step="1"
			value={$chunks.contextLength}
			class="w-1/2 rounded py-1.5 px-4 text-sm dark:text-gray-300 dark:bg-gray-800 outline-none border border-gray-100 dark:border-gray-600"
		/>
	</div>

	<div class="py-0.5 flex justify-end">
		<button
			class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
			on:click={() => sendToAPI()}
		>
			Enviar
		</button>
	</div>

	<hr class=" dark:border-gray-700" />
	<div class="text-sm font-medium">Ajustes de la base de datos</div>

	<div class="flex flex-col">
		<div class="flex">
			<button
				class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition bg-gray-200 dark:bg-gray-700 s--7fsHGLC475o"
				on:click={() => deleteInfo()}
			>
				<div class="self-center mr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="w-5 h-5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
						/>
					</svg>
				</div>
				<div class="self-center">Borrar base de datos</div>
			</button>
		</div>
	</div>
</div>
