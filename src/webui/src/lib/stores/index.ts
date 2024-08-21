import { writable } from "svelte/store";

// Backend
export const info = writable({});

// Frontend
export const db = writable(undefined);
export const chatId = writable("");
export const chats = writable([]);
export const chunks = writable({
	chunkLength: 700,
	contextLength: 200
});
export const settings = writable({});
export const showSettings = writable(false);
