'use strict';

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function updateSubscriptionOnServer(subscription, apiEndpoint, csrf_token) {
  return fetch(apiEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-TOKEN': csrf_token
    },
    //body: JSON.stringify(subscription)
    body: JSON.stringify({
      subscription_json: JSON.stringify(subscription)
    })
  });
}

function subscribeUser(swRegistration, applicationServerPublicKey, apiEndpoint, csrf_token) {
  const applicationServerPubKey = urlB64ToUint8Array(applicationServerPublicKey);
  return swRegistration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: applicationServerPubKey
  })
  .then(function(subscription) {
    console.log('User is subscribed.', subscription);

    return updateSubscriptionOnServer(subscription, apiEndpoint, csrf_token);

  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error('Bad status code from server.');
    }
    return response.json();
  })
  .then(function(responseData) {
    if (responseData.status!=="success") {
      throw new Error('Bad response from server.');
    }
  })
  .catch(function(err) {
    console.log('Failed to subscribe the user: ', err);
    console.log(err.stack);
  });
}

function registerServiceWorker(serviceWorkerUrl, applicationServerPublicKey, apiEndpoint, csrf_token){
  let swRegistration = null;
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    console.log('Service Worker and Push is supported');

    navigator.serviceWorker.register(serviceWorkerUrl, { scope: '/' })
    .then(function(swReg) {
      console.log('Service Worker is registered', swReg);
      subscribeUser(swReg, applicationServerPublicKey, apiEndpoint, csrf_token);

      swRegistration = swReg;
    })
    .catch(function(error) {
      console.error('Service Worker Error', error);
    });
  } else {
    console.warn('Push messaging is not supported');
  }
  return swRegistration;
}


