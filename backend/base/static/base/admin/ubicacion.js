// Chained selects on the Inmueble admin form: municipio -> distrito -> barrio.
(function () {
  'use strict';

  function fill(select, options) {
    var current = select.value;
    select.innerHTML = '';
    select.appendChild(new Option('---------', ''));
    options.forEach(function (o) {
      select.appendChild(new Option(o.nombre, o.id, false, String(o.id) === current));
    });
  }

  function load(url, params, select) {
    var query = new URLSearchParams(params).toString();
    return fetch(url + '?' + query, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) { fill(select, data.items); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var municipio = document.getElementById('id_municipio');
    var distrito = document.getElementById('id_distrito');
    var barrio = document.getElementById('id_barrio');
    if (!municipio || !distrito || !barrio) return;
    var url = municipio.dataset.url;

    function reloadBarrios() {
      return load(url, { tipo: 'barrios', municipio: municipio.value, distrito: distrito.value }, barrio);
    }

    municipio.addEventListener('change', function () {
      distrito.value = '';
      barrio.value = '';
      load(url, { tipo: 'distritos', municipio: municipio.value }, distrito).then(reloadBarrios);
    });
    distrito.addEventListener('change', function () {
      barrio.value = '';
      reloadBarrios();
    });
  });
})();
