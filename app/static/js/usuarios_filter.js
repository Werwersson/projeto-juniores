/**
 * Filtro e busca da página de Usuários (Supervisor).
 * Separado em arquivo externo para cumprir a Content-Security-Policy.
 */
(function () {
  var filtroAtivo = 'todos';
  var tabela      = document.getElementById('tabela-usuarios');
  var buscaInput  = document.getElementById('busca-usuario');
  var semRes      = document.getElementById('sem-resultados');

  if (!tabela) return;

  function aplicarFiltros() {
    var busca    = buscaInput ? buscaInput.value.toLowerCase().trim() : '';
    var rows     = tabela.querySelectorAll('tbody tr[data-role]');
    var visiveis = 0;

    for (var i = 0; i < rows.length; i++) {
      var row     = rows[i];
      var roleOk  = (filtroAtivo === 'todos' || row.getAttribute('data-role') === filtroAtivo);
      var nomeOk  = (busca === '' || (row.getAttribute('data-nome') || '').indexOf(busca) !== -1);
      var mostrar = roleOk && nomeOk;
      row.style.display = mostrar ? '' : 'none';
      if (mostrar) visiveis++;
    }

    if (semRes) semRes.style.display = (visiveis === 0) ? '' : 'none';
  }

  // Filtro por role — clique nos botões
  var btns = document.querySelectorAll('.filtro-btn');
  for (var j = 0; j < btns.length; j++) {
    (function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        for (var k = 0; k < btns.length; k++) btns[k].classList.remove('active');
        btn.classList.add('active');
        filtroAtivo = btn.getAttribute('data-role');
        aplicarFiltros();
      });
    })(btns[j]);
  }

  // Busca por nome — digitar no input
  if (buscaInput) {
    buscaInput.addEventListener('input', function () {
      aplicarFiltros();
    });
  }
})();
