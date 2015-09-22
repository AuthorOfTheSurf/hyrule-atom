// [FIXME]
function double(method, n) {
  if (method === 'double') {
    return 2 * n
  } else if (method === 'triple') {
    return 3 * n
  }
  // ... :(
}

// -- OK, I fixed it
function multiply(m, n) {
  return m * n
}

// [TODO] add more tests
var input1 = "{hi()()[[[[]]]]}"
var input2 = "{[(...[....)]}"
var input3 = "{()}"
var input4 = ""

function isWellBraced(s) {
  var stack = []
  var braces = {
    '{': '}',
    '[': ']',
    '(': ')'
  }
  // either an opening brace, or a matching closing brace
  s.split('').forEach(function (c) {
    if (braces[c]) {
      stack.push(braces[c])
    } else if (stack[stack.length-1] === c) {
      stack.pop()
    }
  })
  return stack.length === 0
}

[input1, input2, input3, input4].forEach(function (s) {
  console.log(isWellBraced(s))
})
