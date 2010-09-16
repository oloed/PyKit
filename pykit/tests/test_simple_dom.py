from monocle import _o
import monocle.util

@_o
def test_dom_behaviour(ctx):
    body = ctx.document.firstChild.firstChild.nextSibling
    body.innerHTML = "<div>hello <em>world!</em></div>"
    yield monocle.util.sleep(.5)
    div = body.firstChild
    assert div.nodeName == 'DIV'
    assert div.innerText == "hello world!"
    assert div.innerHTML == "hello <em>world!</em>"

@_o
def test_javascript(ctx):
    assert ctx.window.eval('1+1') == 2
    assert ctx.window.eval('var c = 33; c - 20;') == 13

    ctx.window.eval('document.firstChild.innerHTML = "asdf";')
    assert ctx.document.firstChild.innerHTML == "asdf"

    dic = ctx.window.eval('window.pykittest_dict = {a: 13, b: {c: 22}}; '
                          'pykittest_dict')
    assert dic['a'] == 13 and dic['b']['c'] == 22

    dic['a'] = 25
    assert ctx.window.eval('pykittest_dict.a') == 25

    func = ctx.window.eval('window.pykittest_func = function(n){return n+3;}; '
                           'pykittest_func')

    assert repr(ctx.window.eval('[4, 123]')) == '<JavaScript 4,123>'

@_o
def test_javascript_methods(ctx):
    ctx.window.eval('window.pykittest_callback = function(n){return n+6;};')
    assert ctx.window.pykittest_callback(10) == 16

    calls = []
    @ctx.window._callback
    def call_to_python(this, *args):
        calls.append( (this, args) )
    ctx.window.eval('window.call_me_back = function(f) {\n'
                    '    f(); f(1, 3);\n'
                    '    var ob = {f: f, n: 13}; ob.f(); ob.f("asdf");\n'
                    '};')
    ctx.window.call_me_back(call_to_python)
    assert len(calls) == 4
    assert calls[0][0]._obj is ctx.window._obj
    assert calls[1][1] == (1, 3)
    assert calls[2][0]['n'] == 13
    assert calls[3][1] == ("asdf",)

@_o
def test_javascript_method_exceptions(ctx):
    ctx.window.eval('window.crashme = function(){ something.non.existent; }')
    try:
        ctx.window.crashme()
    except Exception, e:
        from pykit.driver.cocoa_dom import ScriptException
        assert isinstance(e, ScriptException)
        assert e.args[0] == "ReferenceError: Can't find variable: something"
    else:
        assert False, "should raise exception"

@_o
def test_javascript_method_arguments(ctx):
    ctx.window.eval('window.whatis = function(arg) { '
                    'return {type: typeof(arg), str: ""+arg}; }')
    what = ctx.window.whatis
    def assert_what(value, js_type, js_str):
        out = what(value)
        assert out['type'] == js_type, "%r != %r" % (out['type'], js_type)
        assert out['str'] == js_str, "%r != %r" % (out['str'], js_str)

    assert_what(1, 'number', '1')
    assert_what("asdf", 'string', 'asdf')
    assert_what([1,2,"asdf"], 'object', '1,2,asdf')
    assert_what({'a': 'b'}, 'object', '{\n    a = b;\n}')
    assert_what(True, 'boolean', 'true')
    assert_what(None, 'object', 'null')

    class C(object):
        def __repr__(self): return "<:)>"
    assert_what(C(), 'object', '<:)>')

    # auto-unwrap wrapped arguments
    assert_what(what, 'function', ('function (arg) { return {type: '
                                   'typeof(arg), str: ""+arg}; }') )

    assert_what(ctx.window['document'], 'object', '[object HTMLDocument]')

@_o
def test_javascript_eval(ctx):
    ev = ctx.window.eval
    assert ev('') is None
    assert ev('null') is None
    assert ev('13') == 13
    assert ev('"hi"') == "hi"
    assert ev('1+2') == 3
    assert ev('(function(){var c=3; return c+5;})()') == 8

    try:
        ev('---')
    except Exception, e:
        from pykit.driver.cocoa_dom import ScriptException
        assert isinstance(e, ScriptException)
        assert e.args[0] == 'SyntaxError: Parse error'
    else:
        assert False, "should raise exception"

all_tests = [test_dom_behaviour, test_javascript,
             test_javascript_methods, test_javascript_method_exceptions,
             test_javascript_method_arguments, test_javascript_eval]
