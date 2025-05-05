const CACHE_NAME = 'itpot-cache-v1';
const ASSETS_TO_CACHE = [
  '/',                                      
  '/static/css/base.css',                  
  '/static/css/admin/all.css',              
  '/static/img/logo/Logo.png',  
  '/static/img/logo/applogo.png',            
  '/static/img/logo/Logo_Text_Right.png',   
  '/static/manifest.json',                  
   '/static/css/cart.css', 
   '/static/css/contact.css',
   '/static/css/index-style.css',
   '/static/css/shop-style.css',
   '/static/css/team-style.css',
   '/static/css/admin/login.css',
   'static/img/product3.jpg',
   'static/img/product1.jpg',
   'static/img/product2.jpg',
   'static/img/pexels-vlad-fonsark-2175898-4095495.jpg',
   'static/img/pexels-pixabay-259955.jpg',
   'static/img/pexels-nipananlifestyle-com-625927-1581484.jpg',
   'static/img/pexels-ngo-tr-ng-an-837314-1717767.jpg',
   'static/img/HKobo9Zd8vTYdFcb-generated_image.jpg',
   'static/img/about-img.png',
   'static/img/Contact-Images/cupatea.JPG',
   'static/img/Contact-Images/email.png',
   'static/img/Contact-Images/facebook.png',
   'static/img/Contact-Images/Friends.jpg',
   'static/img/Contact-Images/instagram.png',
   'static/img/Contact-Images/pin.png',
   'static/img/Contact-Images/telephone.png',
   'static/img/Contact-Images/twitter.png',
   '/static/img/Team/Becca.jpg',
   '/static/img/Team/Jess.JPG',
   '/static/img/Team/Karen Oswald.jpg',
   '/static/img/Team/Marc Franco.JPG',


];


self.addEventListener('install', event => {
    event.waitUntil(
      caches.open(CACHE_NAME)
        .then(cache => cache.addAll(ASSETS_TO_CACHE))
        .then(() => {
          console.log('Service Worker: Install successful, assets cached');
          return self.skipWaiting();
        })
        .catch(err => {
          console.error('Service Worker: Install failed:', err);
        })
    );
  });

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
});


self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then(networkResponse => {

        return networkResponse;
      });
    })
  );
});