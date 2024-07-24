<script lang="ts">
	import Modal from "../common/Modal.svelte";
	import Remoto from "./Settings/Remoto.svelte";
	import General from "./Settings/General.svelte";
	import About from "./Settings/About.svelte";
	import Local from "./Settings/Local.svelte";


	export let show = false;
	let selectedTab = "general";
</script>

<Modal bind:show>
	<div>
		<div class=" flex justify-between dark:text-gray-300 px-5 py-4">
			<div class=" text-lg font-medium self-center">Ajustes</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<hr class=" dark:border-gray-800" />

		<div class="flex flex-col md:flex-row w-full p-4 md:space-x-4">
			<div
				class="tabs flex flex-row overflow-x-auto space-x-1 md:space-x-0 md:space-y-1 md:flex-col flex-1 md:flex-none md:w-40 dark:text-gray-200 text-xs text-left mb-3 md:mb-0"
			>
				<button
					class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition {selectedTab ===
					'general'
						? 'bg-gray-200 dark:bg-gray-700'
						: ' hover:bg-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => {
						selectedTab = "general";
					}}
				>
					<div class=" self-center mr-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M8.34 1.804A1 1 0 019.32 1h1.36a1 1 0 01.98.804l.295 1.473c.497.144.971.342 1.416.587l1.25-.834a1 1 0 011.262.125l.962.962a1 1 0 01.125 1.262l-.834 1.25c.245.445.443.919.587 1.416l1.473.294a1 1 0 01.804.98v1.361a1 1 0 01-.804.98l-1.473.295a6.95 6.95 0 01-.587 1.416l.834 1.25a1 1 0 01-.125 1.262l-.962.962a1 1 0 01-1.262.125l-1.25-.834a6.953 6.953 0 01-1.416.587l-.294 1.473a1 1 0 01-.98.804H9.32a1 1 0 01-.98-.804l-.295-1.473a6.957 6.957 0 01-1.416-.587l-1.25.834a1 1 0 01-1.262-.125l-.962-.962a1 1 0 01-.125-1.262l.834-1.25a6.957 6.957 0 01-.587-1.416l-1.473-.294A1 1 0 011 10.68V9.32a1 1 0 01.804-.98l1.473-.295c.144-.497.342-.971.587-1.416l-.834-1.25a1 1 0 01.125-1.262l.962-.962A1 1 0 015.38 3.03l1.25.834a6.957 6.957 0 011.416-.587l.294-1.473zM13 10a3 3 0 11-6 0 3 3 0 016 0z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class=" self-center">General</div>
				</button>

				<button
					class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition {selectedTab ===
					'Remoto'
						? 'bg-gray-200 dark:bg-gray-700'
						: ' hover:bg-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => {
						selectedTab = "remoto";
					}}
				>
					<div class=" self-center mr-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								d="M17 2.75a.75.75 0 00-1.5 0v5.5a.75.75 0 001.5 0v-5.5zM17 15.75a.75.75 0 00-1.5 0v1.5a.75.75 0 001.5 0v-1.5zM3.75 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5a.75.75 0 01.75-.75zM4.5 2.75a.75.75 0 00-1.5 0v5.5a.75.75 0 001.5 0v-5.5zM10 11a.75.75 0 01.75.75v5.5a.75.75 0 01-1.5 0v-5.5A.75.75 0 0110 11zM10.75 2.75a.75.75 0 00-1.5 0v1.5a.75.75 0 001.5 0v-1.5zM10 6a2 2 0 100 4 2 2 0 000-4zM3.75 10a2 2 0 100 4 2 2 0 000-4zM16.25 10a2 2 0 100 4 2 2 0 000-4z"
							/>
						</svg>
					</div>
					<div class=" self-center">Descarga remota</div>
				</button>

				<button
					class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition {selectedTab ===
					'local'
						? 'bg-gray-200 dark:bg-gray-700'
						: ' hover:bg-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => {
						selectedTab = "local";
					}}
				>
					<div class=" self-center mr-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37zM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 013 13.179z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class=" self-center">Importación local</div>
				</button>

				<button
					class="px-2.5 py-2.5 min-w-fit rounded-lg flex-1 md:flex-none flex text-right transition {selectedTab ===
					'about'
						? 'bg-gray-200 dark:bg-gray-700'
						: ' hover:bg-gray-300 dark:hover:bg-gray-800'}"
					on:click={() => {
						selectedTab = "about";
					}}
				>
					<div class=" self-center mr-2">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-4 h-4"
						>
							<path
								fill-rule="evenodd"
								d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class=" self-center">Acerca de</div>
				</button>
			</div>
			<div class="flex-1 md:min-h-[340px]">
				{#if selectedTab === "general"}
					<div class="flex flex-col h-full justify-between text-sm">
						<div class=" space-y-3 pr-1.5 overflow-y-scroll max-h-72">
							<div class=" text-sm font-medium">Ajustes de la interfaz</div>
							<General />
						</div>					
					</div>
				{:else if selectedTab === "local"}
					<div class="flex flex-col h-full justify-between text-sm">
						<div class=" space-y-3 pr-1.5 overflow-y-scroll max-h-72">
							<div class=" text-sm font-medium">Importación local de documentos del BOE</div>
							<Local/>
						</div>					
				</div>

				{:else if selectedTab === "remoto"}
					<div class="flex flex-col h-full justify-between text-sm">
						<div class=" space-y-3 pr-1.5 overflow-y-scroll max-h-72">
							<div class=" text-sm font-medium">Descarga remota de documentos del BOE</div>
							<Remoto/>
						</div>					
					</div>
				
				{:else if selectedTab === "about"}
				<div class="flex flex-col h-full justify-between text-sm">
					<div class=" space-y-3 pr-1.5 overflow-y-scroll max-h-72">
						<About/>
					</div>					
				</div>
				{/if}
			</div>
		</div>
	</div>
</Modal>

<style>
	.tabs::-webkit-scrollbar {
		display: none; /* for Chrome, Safari and Opera */
	}

	.tabs {
		-ms-overflow-style: none; /* IE and Edge */
		scrollbar-width: none; /* Firefox */
	}

</style>
