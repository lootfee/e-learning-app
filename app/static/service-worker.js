'use strict';

/* eslint-enable max-len */

self.addEventListener('install', function(event) {
  console.log('Service Worker installing.');
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker activating.');
});

self.addEventListener('fetch', function (event) {
  console.log('Fetch activated')
    // it can be empty if you just want to get rid of that error
});

self.addEventListener('push', function (event) {
  if ('actions' in Notification.prototype) {
    console.log('Action buttons are supported.')
  } else {
    console.log('// Action buttons are NOT supported.')
  }
});


self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  const pushData = event.data.text();
  console.log(`[Service Worker] Push received this data - "${pushData}"`);
  /*const title = data.title;
  const options = {
    body: data.body,
    icon: 'transparent_logo.ico',
    vibrate: [50, 50, 50],
    // sound: 'static/audio/notification-sound.mp3'
  };*/
  let data, title, body;
  try {
    data = JSON.parse(pushData);
    title = data.title;
    body =  data.body;

  } catch(e) {
    title = "Biogenix App";
    body = pushData;
  }
  const options = {
    body: body,
    icon: 'static/transparent_logo.ico',
    //vibrate: [50, 50, 50],
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});


self.addEventListener('notificationclick', function(e) {
  var notification = e.notification;
  // var primaryKey = notification.data.primaryKey;
  var action = e.action;
  console.log(e)

  var data = JSON.parse(notification.data);

  if (action === 'close') {
    notification.close();
  } else {
    if (data.data.html){
      clients.openWindow(data.html);
      notification.close();
    }

  }
});