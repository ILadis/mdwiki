!function (global) {

  function hook() {
    var index = 1;
    var checkboxes = document.querySelectorAll('input[type=checkbox]');

    for (var checkbox of checkboxes) {
      checkbox.disabled = false;
      checkbox.addEventListener('click', tick.bind(this, index++, checkbox));
    }
  }

  function tick(index, checkbox) {
    var action = checkbox.checked ? 'tick' : 'untick';
    var article = document.querySelector('article');

    var url = `../index.php/apps/notes/api/v1/notes/${article.id}/checkboxes/${index}/${action}`;

    fetch(url, { method: "POST" });
  }

  global.addEventListener('load', hook);

}(window);
