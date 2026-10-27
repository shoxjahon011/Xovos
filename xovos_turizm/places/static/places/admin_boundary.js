document.addEventListener('DOMContentLoaded', function () {
  var el = document.getElementById('id_border');
  if (!el) return;

  function num(v) { return parseFloat(String(v).replace(',', '.')); }

  var row = el.closest('.form-row') || el.parentNode;
  var wrap = document.createElement('div');
  wrap.style.cssText = 'margin:10px 0;';
  wrap.innerHTML =
    '<p style="margin:0 0 6px;color:#555">' +
    "Tuman chegarasi bo'ylab ketma-ket bosing (soat strelkasi bo'yicha). " +
    "Nuqtani sudrab surish mumkin. Chegara chizig'ini ko'rish uchun o'ng yuqoridan " +
    "<b>Xarita</b> rejimini tanlang. Burilishlarda ko'proq nuqta qo'ying." +
    '</p>' +
    '<div style="margin-bottom:6px">' +
    '<input id="bsearch" type="text" placeholder="Joy qidirish (masalan: Xovos)" ' +
    'style="padding:6px;width:260px"> ' +
    '<button type="button" id="bgo" style="padding:6px 10px">Topish</button></div>' +
    '<div id="bmap" style="height:560px;width:100%;max-width:900px;border:1px solid #ccc"></div>' +
    '<div style="margin-top:6px">' +
    '<button type="button" id="bundo" style="margin-right:8px;padding:6px 10px">↩ Oxirgi nuqtani o\'chirish</button>' +
    '<button type="button" id="bclear" style="padding:6px 10px">🗑 Hammasini tozalash</button>' +
    '<span id="bcount" style="margin-left:12px;color:#555"></span></div>';
  row.parentNode.insertBefore(wrap, row);

  var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  });
  var sat = L.layerGroup([
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {maxNativeZoom: 17, maxZoom: 19}),
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      {maxNativeZoom: 17, maxZoom: 19})
  ]);
  var map = L.map('bmap', {layers: [osm]}).setView([40.2, 68.77], 10);
  L.control.layers({'🗺 Xarita': osm, '🛰 Sputnik': sat}, null, {collapsed: false}).addTo(map);

  var pts = [];
  var poly = L.polygon([], {color: '#e91e63', weight: 3, fillOpacity: 0.12}).addTo(map);
  var handles = L.layerGroup().addTo(map);
  var count = document.getElementById('bcount');

  function parse() {
    pts = [];
    el.value.split('\n').forEach(function (ln) {
      var p = ln.replace(';', ',').split(',');
      if (p.length >= 2) {
        var a = num(p[0]), b = num(p[1]);
        if (!isNaN(a) && !isNaN(b)) pts.push([a, b]);
      }
    });
  }

  function save() {
    el.value = pts.map(function (p) {
      return p[0].toFixed(6) + ', ' + p[1].toFixed(6);
    }).join('\n');
    count.textContent = 'Nuqtalar: ' + pts.length;
  }

  function draw(fit) {
    poly.setLatLngs(pts);
    handles.clearLayers();
    pts.forEach(function (p, i) {
      var m = L.marker(p, {
        draggable: true,
        icon: L.divIcon({
          className: '', iconSize: [14, 14], iconAnchor: [7, 7],
          html: '<div style="width:14px;height:14px;border-radius:50%;background:' +
                (i === 0 ? '#2e7d32' : '#e91e63') + ';border:2px solid #fff"></div>'
        })
      }).addTo(handles);
      m.on('drag', function (e) {
        pts[i] = [e.latlng.lat, e.latlng.lng];
        poly.setLatLngs(pts);
      });
      m.on('dragend', save);
    });
    count.textContent = 'Nuqtalar: ' + pts.length;
    if (fit && pts.length > 2) map.fitBounds(poly.getBounds(), {padding: [30, 30]});
  }

  map.on('click', function (e) {
    pts.push([e.latlng.lat, e.latlng.lng]);
    save();
    draw(false);
  });

  document.getElementById('bundo').onclick = function () { pts.pop(); save(); draw(false); };
  document.getElementById('bclear').onclick = function () {
    if (confirm("Barcha nuqtalar o'chirilsinmi?")) { pts = []; save(); draw(false); }
  };
  el.addEventListener('change', function () { parse(); draw(true); });

  function search() {
    var q = document.getElementById('bsearch').value.trim();
    if (!q) return;
    fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' + encodeURIComponent(q))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.length) map.setView([parseFloat(d[0].lat), parseFloat(d[0].lon)], 11);
        else alert('Topilmadi');
      })
      .catch(function () { alert('Qidiruv ishlamadi'); });
  }
  document.getElementById('bgo').onclick = search;
  document.getElementById('bsearch').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); search(); }
  });

  parse();
  draw(true);
});