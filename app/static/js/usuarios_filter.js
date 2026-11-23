/**
 * Filtro, busca e ordenação da página de Usuários (Supervisor).
 */
(function () {
  var filtroAtivo = 'todos';
  var tabela      = document.getElementById('tabela-usuarios');
  var buscaInput  = document.getElementById('busca-usuario');
  var semRes      = document.getElementById('sem-resultados');
  var ordemSelect = document.getElementById('ordem-usuarios');

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

  function ordenarTabela(criterio) {
    var tbody = tabela.querySelector('tbody');
    var rows  = Array.from(tbody.querySelectorAll('tr[data-role]'));

    rows.sort(function (a, b) {
      if (criterio === 'papel-nome') {
        var rA = parseInt(a.getAttribute('data-role-order') || '9', 10);
        var rB = parseInt(b.getAttribute('data-role-order') || '9', 10);
        if (rA !== rB) return rA - rB;
        return (a.getAttribute('data-nome') || '').localeCompare(b.getAttribute('data-nome') || '', 'pt-BR');
      } else if (criterio === 'nome-asc') {
        return (a.getAttribute('data-nome') || '').localeCompare(b.getAttribute('data-nome') || '', 'pt-BR');
      } else if (criterio === 'nome-desc') {
        return (b.getAttribute('data-nome') || '').localeCompare(a.getAttribute('data-nome') || '', 'pt-BR');
      } else if (criterio === 'premiles-desc') {
        var sA = parseInt(a.getAttribute('data-saldo') || '0', 10);
        var sB = parseInt(b.getAttribute('data-saldo') || '0', 10);
        if (sB !== sA) return sB - sA;
        return (a.getAttribute('data-nome') || '').localeCompare(b.getAttribute('data-nome') || '', 'pt-BR');
      }
      return 0;
    });

    rows.forEach(function (r) { tbody.appendChild(r); });
    aplicarFiltros();
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

  // Busca por nome
  if (buscaInput) {
    buscaInput.addEventListener('input', function () {
      aplicarFiltros();
    });
  }

  // Mudança no select de ordenação
  if (ordemSelect) {
    ordemSelect.addEventListener('change', function () {
      ordenarTabela(ordemSelect.value);
    });
  }

  var sortNomeAsc = true;
  window.alternarOrdem = function (col) {
    if (col === 'nome') {
      var novoCriterio = sortNomeAsc ? 'nome-asc' : 'nome-desc';
      sortNomeAsc = !sortNomeAsc;
      if (ordemSelect) ordemSelect.value = novoCriterio;
      ordenarTabela(novoCriterio);
    } else if (col === 'papel') {
      if (ordemSelect) ordemSelect.value = 'papel-nome';
      ordenarTabela('papel-nome');
    } else if (col === 'premiles') {
      if (ordemSelect) ordemSelect.value = 'premiles-desc';
      ordenarTabela('premiles-desc');
    }
  };
})();
