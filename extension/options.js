const key1El  = document.getElementById('key1');
const key2El  = document.getElementById('key2');
const msgEl   = document.getElementById('msg');
const saveBtn = document.getElementById('save');

chrome.storage.local.get(['api_keys', 'default_provider'], result => {
  const apiKeys = result.api_keys || {};
  const keys    = apiKeys.groq || [];
  if (keys[0]) key1El.value = keys[0];
  if (keys[1]) key2El.value = keys[1];
});

saveBtn.addEventListener('click', async () => {
  const k1 = key1El.value.trim();
  const k2 = key2El.value.trim();

  if (!k1) {
    msgEl.textContent = 'Please enter at least Key 1.';
    msgEl.className   = 'err';
    return;
  }

  const keys = [k1];
  if (k2) keys.push(k2);

  const stored  = await chrome.storage.local.get(['api_keys', 'default_provider']);
  const apiKeys = stored.api_keys || {};
  apiKeys.groq  = keys;

  await chrome.storage.local.set({
    api_keys: apiKeys,
    default_provider: stored.default_provider || 'groq'
  });

  msgEl.textContent = `✅ ${keys.length} key(s) saved! You're all set.`;
  msgEl.className   = '';
});
