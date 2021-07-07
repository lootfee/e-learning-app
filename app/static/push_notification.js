// Push Notifications
/*const pushButton = document.getElementById('push-btn');
if (pushButton){
  pushButton.addEventListener('click', askPermission);
  notificationButtonUpdate();

  if (!("Notification" in window)) {
      pushButton.hidden;
    }
}*/

/*function askPermission(evt) {
  pushButton.disabled = true;
  Notification.requestPermission().then(function(permission) { notificationButtonUpdate(); });

}*/

/*function askPermission() {
  // pushButton.disabled = true;
  return new Promise(function(resolve, reject) {
    const permissionResult = Notification.requestPermission(function(result) {
      resolve(result);
    });
  console.log(permissionResult)
    if (permissionResult) {
      permissionResult.then(resolve, reject);
    }
  })
  .then(function(permissionResult) {
    notificationButtonUpdate();
    if (permissionResult !== 'granted') {
      throw new Error('We weren\'t granted permission.');
    }
  });
}

function notificationButtonUpdate() {
  if (Notification.permission == 'granted') {
    pushButton.disabled = true;
  } else {
    pushButton.disabled = false;
  }
}*/



