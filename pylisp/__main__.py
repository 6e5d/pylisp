import sys
from pyltr import parse_flat, dump

class StackTrace(Exception):
	pass

true = ["quote", "t"]
nil = ["quote", []]
class Ctx:
	def __init__(self, parent, name):
		self.parent = parent
		self.data = dict()
		self.name = name
		self.stack = []
	def __contains__(self, x):
		if x in self.data:
			if x in self.data:
				return True
		if self.parent == None:
			return None
		return x in self.parent
	def __getitem__(self, x):
		if x in self.data:
			return self.data[x]
		if self.parent == None:
			raise StackTrace(f"get {x} notin env", self)
		return self.parent[x]
	def __setitem__(self, x, y):
		self.data[x] = y
	def print_nonfunc(self):
		if self.parent != None:
			self.parent.print_nonfunc()
		for k, v in self.data.items():
			if v[0] in ["label", "lambda"]:
				continue
			print(k, v)
	def depth(self):
		if self.parent != None:
			return self.parent.depth() + 1
		return 0
def uq(expr):
	assert isinstance(expr, list)
	assert expr[0] == "quote"
	return expr[1]
def tobool(x):
	if x:
		return true
	else:
		return nil
def checklist(x):
	return x[0] == "quote" and isinstance(x[1], list)
def car(expr, ctx):
	v = ev2(expr, ctx)
	if not checklist(v):
		raise StackTrace(f"car a nonlist {v}", ctx)
	if v[1] == []:
		raise StackTrace("car empty list", ctx)
	return ["quote", uq(v)[0]]
def cdr(expr, ctx):
	v = ev2(expr, ctx)
	checklist(v)
	return ["quote", uq(v)[1:]]
def consb(x, y):
	return ["quote", [x] + y]
def cons(x, y, ctx):
	x = ev2(x, ctx)
	y = ev2(y, ctx)
	checklist(y)
	x = uq(x)
	y = uq(y)
	return consb(x, y)
def atomb(expr):
	if not isinstance(expr, list) or len(expr) != 2 or expr[0] != "quote":
		return False
	expr = uq(expr)
	return isinstance(expr, str) or expr == []
def atom(expr, ctx):
	ctx.stack.append(1)
	expr = ev2(expr, ctx)
	ctx.stack.pop()
	result = atomb(expr)
	print("atom?", expr, result)
	return tobool(result)
def eq(x, y, ctx):
	ctx.stack.append(1)
	x = ev2(x, ctx)
	ctx.stack[-1] = 2
	y = ev2(y, ctx)
	ctx.stack.pop()
	if not atomb(x):
		return nil
	if not atomb(y):
		return nil
	return tobool(x == y)
def cond(exprs, ctx):
	ctx.stack.append(0)
	for [p, x] in exprs:
		ctx.stack[-1] += 1
		ctx.stack.append(0)
		result = ev2(p, ctx)
		ctx.stack[-1] = 1
		# print(p, x, result, ctx.data)
		if true == result:
			print("COND SATISFIED, GOTO", dump(x))
			return ev2(x, ctx)
	raise Exception("cond exhaust")
def ev(e, a):
	e = uq(e)
	return ev2(e, a)
def ev2(e, a):
	if isinstance(e, str):
		return a[e]
	assert isinstance(e, list)
	if isinstance(e[0], str):
		match e[0]:
			case "quote":
				return e # uq is handled in ev
			case "atom":
				return atom(e[1], a)
			case "eq":
				return eq(e[1], e[2], a)
			case "car":
				return car(e[1], a)
			case "cdr":
				return cdr(e[1], a)
			case "cons":
				return cons(e[1], e[2], a)
			case "cond":
				return cond(e[1:], a)
			case "display":
				v = ev2(e[1], a)
				print("display:", v)
				return v
			case x:
				# application, a[e[0]] must be lambda
				call = [a[e[0]]] + e[1:]
				return ev2(call, a)
	match e[0][0]:
		case "label":
			a2 = Ctx(a, e[0][1])
			a2[e[0][1]] = e[0] # recursion
			call = consb(e[0][2], e[1:])
			return ev(call, a2)
		case "lambda":
			a.stack.append(1)
			e1 = [ev2(ee, a) for ee in e[1:]]
			a2 = Ctx(a, "")
			assert len(e[0][1]) == len(e1)
			a.stack.append(0)
			for var, val in zip(e[0][1], e1):
				a.stack[-1] += 1
				a[var] = val
			a.stack.pop()
			a.stack.append(0)
			a.stack.append(2)

			print("=========================")
			print(a2.depth(), "call", e[0][2])
			a2.print_nonfunc()
			result = ev2(e[0][2], a2)
			print(a2.depth(), "exit")
			a.stack.pop()
			a.stack.pop()
			return result
		case x:
			raise Exception(e)

expr = parse_flat(sys.stdin.read())
ctx = Ctx(None, "ENTRANCE")
for ee in expr:
	ctx[ee[1]] = ee
try:
	print(ev(["quote", [ctx["main"]]], ctx))
except StackTrace as e:
	print(f"ERROR! {e.args[0]} >>>")
	a = e.args[1]
	a.print_nonfunc()
	while a != None:
		if a.name not in ctx:
			print("unknown", a.stack)
		else:
			print(a.name, a.stack)
		a = a.parent
	print("ERROR! trace end <<<")
	raise e
