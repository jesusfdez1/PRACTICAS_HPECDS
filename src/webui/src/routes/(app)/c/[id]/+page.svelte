<script lang="ts">
	import { v4 as uuidv4 } from 'uuid';
	import toast from 'svelte-french-toast';

	import { OLLAMA_API_BASE_URL, API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT } from '$lib/constants';
	import { tick } from 'svelte';
	import { convertMessagesToHistory, splitStream } from '$lib/utils';
	import { goto } from '$app/navigation';
	import { settings, db, chats, chatId } from '$lib/stores';

	import MessageInput from '$lib/components/chat/MessageInput.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import { page } from '$app/stores';

	let loaded = false;
	let stopResponseFlag = false;
	let autoScroll = true;

	// let chatId = $page.params.id;

	let title = '';
	let prompt = '';

	let messages = [];
	let history = {
		messages: {},
		currentId: null
	};

	$: if (history.currentId !== null) {
		let _messages = [];

		let currentMessage = history.messages[history.currentId];
		while (currentMessage !== null) {
			_messages.unshift({ ...currentMessage });
			currentMessage =
				currentMessage.parentId !== null ? history.messages[currentMessage.parentId] : null;
		}
		messages = _messages;
	} else {
		messages = [];
	}

	$: if ($page.params.id) {
		(async () => {
			let chat = await loadChat();

			await tick();
			if (chat) {
				loaded = true;
			} else {
				await goto('/');
			}
		})();
	}

	//////////////////////////
	// Web functions
	//////////////////////////

	const loadChat = async () => {
		await chatId.set($page.params.id);
		const chat = await $db.getChatById($chatId);

		if (chat) {
			console.log(chat);

			history =
				(chat?.history ?? undefined) !== undefined
					? chat.history
					: convertMessagesToHistory(chat.messages);
			title = chat.title;

			let _settings = JSON.parse(localStorage.getItem('settings') ?? '{}');
			await settings.set({
				..._settings,
				system: chat.system ?? _settings.system,
			});
			autoScroll = true;

			await tick();
			if (messages.length > 0) {
				history.messages[messages.at(-1).id].done = true;
			}
			await tick();

			return chat;
		} else {
			return null;
		}
	};

	const copyToClipboard = (text) => {
		if (!navigator.clipboard) {
			var textArea = document.createElement('textarea');
			textArea.value = text;

			// Avoid scrolling to bottom
			textArea.style.top = '0';
			textArea.style.left = '0';
			textArea.style.position = 'fixed';

			document.body.appendChild(textArea);
			textArea.focus();
			textArea.select();

			try {
				var successful = document.execCommand('copy');
				var msg = successful ? 'successful' : 'unsuccessful';
				console.log("Fallback: El comando de copiar texto fue " + msg);
			} catch (err) {
				console.error("Fallback: Oops, no se pudo copiar", err);
			}

			document.body.removeChild(textArea);
			return;
		}
		navigator.clipboard.writeText(text).then(
			function () {
				console.log("Async: ¡El texto se ha copiado al portapapeles correctamente!");
			},
			function (err) {
				console.error("Async: No se pudo copiar el texto: ", err);
			}
		);
	};

	//////////////////////////
	// Ollama functions
	//////////////////////////

	const sendPrompt = async (userPrompt, parentId, _chatId) => {
		await Promise.all(
				sendPromptOllama(userPrompt, parentId, _chatId)		
		);

		await chats.set(await $db.getChats());
	};

	const sendPromptOllama = async (userPrompt, parentId, _chatId) => {
		console.log('sendPromptOllama');
		let responseMessageId = uuidv4();
		let responseMessage = {
			parentId: parentId,
			id: responseMessageId,
			childrenIds: [],
			role: 'assistant',
			content: '',
		};

		history.messages[responseMessageId] = responseMessage;
		history.currentId = responseMessageId;
		if (parentId !== null) {
			history.messages[parentId].childrenIds = [
				...history.messages[parentId].childrenIds,
				responseMessageId
			];
		}

		await tick();
		window.scrollTo({ top: document.body.scrollHeight });

		const res = await fetch(`${API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT ?? OLLAMA_API_BASE_URL}/chat`, {
			method: 'POST',
			headers: {
				'Content-Type': 'text/event-stream',
				...($settings.authHeader && { Authorization: $settings.authHeader })
			},
			body: JSON.stringify({
				messages: [
					$settings.system
						? {
								role: 'system',
								content: $settings.system
						  }
						: undefined,
					...messages
				]
					.filter((message) => message)
					.map((message) => ({
						role: message.role,
						content: message.content
					})),
				format: $settings.requestFormat ?? undefined
			})
		}).catch((err) => {
			console.log(err);
			return null;
		});

		if (res && res.ok) {
			const reader = res.body
				.pipeThrough(new TextDecoderStream())
				.pipeThrough(splitStream('\n'))
				.getReader();

			while (true) {
				const { value, done } = await reader.read();
				if (done || stopResponseFlag || _chatId !== $chatId) {
					responseMessage.done = true;
					messages = messages;
					break;
				}

				try {
					let lines = value.split('\n');

					for (const line of lines) {
						if (line !== '') {
							console.log(line);
							let data = JSON.parse(line);

							if ('detail' in data) {
								throw data;
							}

							if (data.done == false) {
								if (responseMessage.content == '' && data.message.content == '\n') {
									continue;
								} else {
									responseMessage.content += data.message.content;
									messages = messages;
								}
							} else {
								responseMessage.done = true;
								responseMessage.context = data.context ?? null;
								responseMessage.info = {
									total_duration: data.total_duration,
									load_duration: data.load_duration,
									sample_count: data.sample_count,
									sample_duration: data.sample_duration,
									prompt_eval_count: data.prompt_eval_count,
									prompt_eval_duration: data.prompt_eval_duration,
									eval_count: data.eval_count,
									eval_duration: data.eval_duration
								};
								messages = messages;

								if ($settings.notificationEnabled && !document.hasFocus()) {
									const notification = new Notification(
										`Asistente el BOE - ${model}`,
										{
											body: responseMessage.content,
											icon: '/favicon.png'
										}
									);
								}

								if ($settings.responseAutoCopy) {
									copyToClipboard(responseMessage.content);
								}
							}
						}
					}
				} catch (error) {
					console.log(error);
					if ('detail' in error) {
						toast.error(error.detail);
					}
					break;
				}

				if (autoScroll) {
					window.scrollTo({ top: document.body.scrollHeight });
				}

				await $db.updateChatById(_chatId, {
					title: title === '' ? 'Chat nuevo' : title,
					system: $settings.system ?? undefined,
					messages: messages,
					history: history
				});
			}
		} else {
			if (res !== null) {
				const error = await res.json();
				console.log(error);
				if ('detail' in error) {
					toast.error(error.detail);
					responseMessage.content = error.detail;
				} else {
					toast.error(error.error);
					responseMessage.content = error.error;
				}
			} else {
				toast.error(`Uh-oh! There was an issue connecting to Ollama.`);
				responseMessage.content = `Uh-oh! There was an issue connecting to Ollama.`;
			}

			responseMessage.error = true;
			responseMessage.content = `Uh-oh! There was an issue connecting to Ollama.`;
			responseMessage.done = true;
			messages = messages;
		}

		stopResponseFlag = false;
		await tick();
		if (autoScroll) {
			window.scrollTo({ top: document.body.scrollHeight });
		}

		if (messages.length == 2 && messages.at(1).content !== '') {
			window.history.replaceState(history.state, '', `/c/${_chatId}`);
			await generateChatTitle(_chatId, userPrompt);
		}
	};

	const submitPrompt = async (userPrompt) => {
		const _chatId = JSON.parse(JSON.stringify($chatId));
		console.log('submitPrompt', _chatId);
			document.getElementById('chat-textarea').style.height = '';

			let userMessageId = uuidv4();
			let userMessage = {
				id: userMessageId,
				parentId: messages.length !== 0 ? messages.at(-1).id : null,
				childrenIds: [],
				role: 'user',
				content: userPrompt,
			};

			if (messages.length !== 0) {
				history.messages[messages.at(-1).id].childrenIds.push(userMessageId);
			}

			history.messages[userMessageId] = userMessage;
			history.currentId = userMessageId;

			await tick();
			if (messages.length == 1) {
				await $db.createNewChat({
					id: _chatId,
					title: 'New Chat',
					system: $settings.system ?? undefined,
					messages: messages,
					history: history
				});
			}

			prompt = '';

			setTimeout(() => {
				window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
			}, 50);

			await sendPrompt(userPrompt, userMessageId, _chatId);
	};

	const stopResponse = () => {
		stopResponseFlag = true;
		console.log('stopResponse');
	};

	const regenerateResponse = async () => {
		const _chatId = JSON.parse(JSON.stringify($chatId));
		console.log('regenerateResponse', _chatId);

		if (messages.length != 0 && messages.at(-1).done == true) {
			messages.splice(messages.length - 1, 1);
			messages = messages;

			let userMessage = messages.at(-1);
			let userPrompt = userMessage.content;

			await sendPrompt(userPrompt, userMessage.id, _chatId);
		}
	};

	const generateChatTitle = async (_chatId, userPrompt) => {
		if ($settings.titleAutoGenerate ?? true) {
			console.log('generateChatTitle');

			const res = await fetch(`${API_MICROSERVICES_BASE_URL + API_MICROSERVICES_PORT ?? OLLAMA_API_BASE_URL}/generate`, {
				method: 'POST',
				headers: {
					'Content-Type': 'text/event-stream',
					...($settings.authHeader && { Authorization: $settings.authHeader })
				},
				body: JSON.stringify({
					prompt: `Genera un título de 3 a 5 palabras para la conversación que empieza con el texto: ${userPrompt}. Responde solo con el título de forma neutral, no puedes agregar nada más, ni comillas ni nada extra, solo el título`,
					stream: false
				})
			})
				.then(async (res) => {
					if (!res.ok) throw await res.json();
					return res.json();
				})
				.catch((error) => {
					if ('detail' in error) {
						toast.error(error.detail);
					}
					console.log(error);
					return null;
				});

			if (res) {
				await setChatTitle(_chatId, res.response === '' ? 'Chat nuevo' : res.response);
			}
		} else {
			await setChatTitle(_chatId, `${userPrompt}`);
		}
	};

	const setChatTitle = async (_chatId, _title) => {
		await $db.updateChatById(_chatId, { title: _title });
		if (_chatId === $chatId) {
			title = _title;
		}
	};
</script>

<svelte:window
	on:scroll={(e) => {
		autoScroll = window.innerHeight + window.scrollY >= document.body.offsetHeight - 40;
	}}
/>

{#if loaded}
	<div class="min-h-screen w-full flex justify-center">
		<div class=" py-2.5 flex flex-col justify-between w-full">
			<div class="max-w-2xl mx-auto w-full px-3 md:px-0 mt-10">
			</div>

			<div class=" h-full mt-10 mb-32 w-full flex flex-col">
				<Messages
					bind:history
					bind:messages
					bind:autoScroll
					{sendPrompt}
					{regenerateResponse}
				/>
			</div>
		</div>

		<MessageInput
			bind:prompt
			bind:autoScroll
			{messages}
			{submitPrompt}
			{stopResponse}
		/>
	</div>
{/if}