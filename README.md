![build](https://github.com/mysticfall/alleycat-reactive/workflows/Python%20application/badge.svg)
# AlleyCat - Reactive

A part of the AlleyCat project which supports the _Reactive Object Pattern_.

## Introduction

AlleyCat Reactive is a project to explore the possibility of bridging the gap between the 
two most widely used programming paradigms, namely, the object-oriented programming (OOP), 
and functional programming (FP).

It aims to achieve its goal by proposing a new design pattern based on the 
[Reactive Extensions (Rx)](http://reactivex.io/).

Even though it is already available on [PyPI repository](https://pypi.org/project/alleycat-reactive/) 
as `alleycat-reactive` package, the project is currently at a proof-of-concept stage 
and highly experimental.

As such, there can be significant changes in the API at any time. Furthermore, the project 
may be discontinued in future if the idea proves to be an unuseful one.

## Reactive Object Pattern

The library provides an API to implement what we term as _Reactive Object Pattern_ or _ROP_ 
for short. Despite its rather pretentious name, it merely means defining class properties 
which can also serve as an _Observable_ in Rx.

But why do we need such a thing?

If you are a seasoned programmer of an OOP language (which includes Python, by the way), 
you may feel like the paradigm already provides everything you need.

On the other hand, if you are already familiar with Rx, you may wonder what OOP has to do 
with the concept, as it's mostly about composing functions, not classes or properties.

Arguably, the most significant benefit that any functional approach brings could be its 
ability to define a process or a value in a declarative manner. 

We won't delve into this subject too much since you can learn about the concept from many 
other websites.

In short, it's much better to define data in a declarative manner, or as "data pipelines", 
especially when it's changing over time. Rx is all about composing and manipulating such 
pipelines in a potentially asynchronous context.

But what if the data does not come from an asynchronous source, like Tweets or GUI events, 
but simple properties objects? Of course, Rx can handle synchronous data as well, but the 
cost of using it may outweigh the benefits in such a scenario.

In a traditional OOP system, properties of an object are mere values which are often 
mutable, but not observable by default. To observe the change of a property over time, we 
must use an observer pattern, usually in the form of a separate event.

Some implementation of Rx allows converting such an event into an _Observable_. Still, it 
can be a tedious task to define an event for every such property, and it requires a lot of 
boilerplate code to convert them into Rx pipelines.

More importantly, the resulting pipelines and their handling code don't have any clear 
relationship with the original object or its properties from which they got derived. They 
are just a bunch of statements which you can put anywhere in the project, and that's not 
how you want to design your business logic in an OOP project.

In a well-designed OOP project, classes form a coherent whole by participating in 
inheritance hierarchies. They may reference, extend, or redefine properties of their 
parents or associated objects to express the behaviours and traits of the domain concepts 
they represent.

And there is another problem with using _Observables_ in such a manner. Once you build an Rx 
pipeline, you can't retrieve the value flowing inside unless you write still more boilerplate 
code to subscribe to the stream and store its value to an outside variable.

This practice is usually discouraged as an anti-pattern, and so is the use of _Subjects_. 
However, the object is not observing some outside data (e.g. Tweets) but owns it, which is 
one of the few cases where the use of a _Subject_ can be justified. In such a context, it's 
perfectly reasonable to assume that an object always has access to a snapshot of all the 
states it owns.

So, what if we can define such state data of an object as _Observables_ which can also 
behave like ordinary properties? Wouldn't it be nice if we can easily access them as in OOP 
while still being able to observe and compose them like in Rx?

And that is what this project is trying to achieve.

## Usage

To achieve the goal outlined in the previous section, we provide a way to define a property 
which can also turn into an _Observable_. And there are two different types of such 
property classes you can use for that purpose.

### Reactive Property

Firstly, there is a type of property that can manage its state, which is implemented by 
`ReactiveProperty[T]` class. To define such a property using an initial value, you can use 
a helper function from_value as follows:

```python
from alleycat.reactive import functions as rv

class Toto:

    # Create an instance of ReactiveProperty[int] with an initial value of '99':
    value = rv.from_value(99) # You know the song, don't you? 
```

Sometimes, you need to determine the initial value by referencing another value supplied 
as a constructor argument. In that case, you can lazily initialize the property by using 
`new_property` as shown below:

```python
from alleycat.reactive import functions as rv

class MyClass:

    # Declare an empty property first.
    value = rv.new_property()

    def __init__(self, init_value: int):

        # Then assign a value as you would do to an ordinary property.
        self.value = init_value
```

Whichever way you choose, it can be read and modified like an ordinary property. If you 
want to make it a read-only property, you can set the `read_only` argument to `True` 
as below:

```python
from alleycat.reactive import functions as rv

class ArcadiaBay:

    writeable = rv.from_value("life is strange")

    read_only = rv.from_value("the past", read_only=True)


place = ArcadiaBay()

print(place.writeable) # "life is strange"
print(place.read_only) # "the past"

place.writeable = "It's awesome"

print(place.writeable) # "It's awesome"

place.read_only = "Let me rewind." # Throws an AttributeError

# Of course, you can't change the past. But the game is hella cool!
```

But haven't we talked about Rx? Of course, we have! And that's the whole point of 
the library, after all.

To convert a reactive property into an _Observable_ of the same type, you can use observe 
method like this:

```python
from alleycat.reactive import functions as rv

class Nena:

    ballons = rv.from_value(98)


nena = Nena()

luftballons = []

rv.observe(nena.ballons).subscribe(luftballons.append) # Returns a Disposable. See Rx API.

print(luftballons) # Returns [98].

nena.ballons = nena.ballons + 1

print(luftballons) # [98, 99] # Ok, I lied before. It's about Nena. not Toto :P
```

If you are familiar with Rx, you may notice the similarities between `ReactiveProperty` 
with _BehaviorSubject_. In fact, the former is a wrapper around the latter, and `observe` 
returns an _Observable_ instance backed by such a subject.

To learn about all the exciting things we can do with an _Observable_, you may want to 
read the official documentation of Rx. We will introduce a few examples later, but before 
that, we better learn about the other variant of the reactive value first.

### Reactive View

ReactiveView is another derivative of _ReactiveValue_, from which `ReactiveProperty` is 
also derived (hence, the alias of `functions` module used above, _"rv"_).

The main difference is that while the latter owns a state value itself, a reactive view 
reflects it from an outside source specified as an _Observable_. To create a reactive 
view from an instance of _Observable_, you can use `from_observable` function like this:

```python
import rx
from alleycat.reactive import functions as rv

class Joni:

    big = rv.from_observable(rx.of("Yellow", "Taxi"))
```

If you are familiar with Rx, you may see it as a wrapper around an _Observable_, while 
a reactive property can be seen as one around a _Subject_.

Like its counterpart, you can initialize a reactive view either eagerly or lazily. In order 
to create a lazy-initializing view, you can use `new_view`, and later provide an _Observable_ 
as shown below:

```python
import rx
from alleycat.reactive import functions as rv

class BothSides:

    love = rv.new_view()

    def __init__(self):
        self.love = rx.of("Moons", "Junes", "Ferris wheels")
```

It also accepts `read_only` option from its constructor (default to `True`, in contrast to the case 
with `ReactiveProperty`) setting of which will make it 'writeable'.

It may sound unintuitive since a 'view' usually implies immutability. However, what changes 
when you set a value of a reactive view is the source _Observable_ that the view monitors, 
not the data itself, as is the case with a reactive property.

Lastly, you can convert a reactive property into a view by calling its `as_view` method. 
It's a convenient shortcut to call `observe` to obtain an _Observable_ of a reactive property 
so that it can be used to initialize an associated view.

The code below shows how you can derive a view from an existing reactive property:

```python
from alleycat.reactive import functions as rv

class Example:

    value = rv.from_value("Boring!") # I know. But it's not easy to make it interesting, alright?  

    view = value.as_view()
```

### Transformation

As we know how to create reactive properties and values, now it's time to learn how to 
transform them. Both variants of `ReactiveValue` provides `map` method, with which you 
can map an arbitrary function or lambda expression over each value in the pipeline:

```python
from alleycat.reactive import functions as rv

class Counter:

    word = rv.new_property()  

    count = word.as_view().map(len).map(lambda c: f"The word has {c} letter(s)")

counter = Counter()

counter.word = "Supercalifragilisticexpialidocious!"

print(counter.count) # Prints "The word has 35 letter(s)". Wait, did you actually count that?
```

But what if you want to use other Rx operators, like `scan` or `merge`? In that case, 
you can use `pipe` just like you would with an _Observable_ instance:

```python
from rx import operators as ops
from alleycat.reactive import functions as rv

class CrowsCounter:
    animal = rv.new_property()

    crows = animal.as_view().pipe(
        ops.map(str.lower),
        ops.filter(lambda v: v == "crow"),
        ops.map(lambda _: 1),
        ops.scan(lambda v1, v2: v1 + v2, 0))

counting = CrowsCounter()

counting.animal = "cat"
counting.animal = "Crow"
counting.animal = "CROW"
counting.animal = "dog"

print(counting.crows) # Returns 2.
```
On a side note, the aggregation performed by `crows` in the above example reports the 
correct value even when there is no explicit subscription in the code. It is because 
all properties and views in this library are published as 'hot' _Observables_ by default.

It was a design decision to make aggregation more intuitive and less error-prone. You 
don't have to understand such an implementation detail unless you come across a problem. 
However, if you have a use case where it would be either necessary or significantly 
efficient to make reactive values 'cold', please feel free to open a feature request.

### Operators

Sometimes, you may need to combine several properties of an object to derive another 
of its attribute. For example, you can merge two or more reactive values to define a 
new one which emits a value whenever one of its sources does, as follows:

```python
from alleycat.reactive import functions as rv

class Fixture:
    cats = rv.new_property()

    dogs = rv.new_property()

    pets = rv.merge(cats, dogs)

pets = []

fixture = Fixture()

rv.observe(fixture, "pets").subscribe(pets.append)

fixture.cats = "Garfield"
fixture.cats = "Grumpy"
fixture.cats = "Cat who argues with a woman over a salad bowl"  # What was his name?

fixture.dogs = "Pompidou"  # Sorry, I'm a cat person so I don't know too many canine celebrities.

print(pets) # The array contains all of the names mentioned above.
```

Imagine you have a `Rectangle` class which declares its `width` and `height` as reactive 
properties. It would be nice if you can somehow define its `area` property based upon 
the rectangle's dimension in a declarative manner.

However, merely merging `width` and `height` properties won't automatically calculate 
the size of the shape. In this case, you can use `combine_latest` to calculate the size 
with the latest values of `width` and `height`, whenever either of them is changed:

```python
from alleycat.reactive import functions as rv

class Rectangle:
    width = rv.new_property(100)

    height = rv.new_property(200)

    area = rv.combine_latest(width, height)(lambda v: v[0] * v[1])

rectangle = Rectangle()

print(rectangle.area) # Prints 20,000... you do the math!

rectangle.width = 150

print(rectangle.area) # Prints 30,000.

rectangle.height = 50

print(rectangle.area) # Prints 750.
```

There's another operator called `zip` whose semantic matches that of the API with the 
same name in Rx. In fact, you can use most of the operators Rx provides by applying them 
over _Observables_ extracted by `combine` method. For instance, you can rewrite the 
above example code  with `combine_latest` operator provided by Rx as follows:

```python
import rx
from alleycat.reactive import functions as rv

class Rectangle:
    width = rv.new_property(100)

    height = rv.new_property(200)

    area = rv.combine(width, height)(rx.combine_latest).map(lambda v: v[0] * v[1])
```

## Install

The library can be installed using `pip` as follows:
```shell script
pip install alleycat-reactive
```

## License
This project is provided under the terms of _[MIT License](LICENSE)_.
