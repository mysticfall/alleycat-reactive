![pytest](https://github.com/mysticfall/alleycat-reactive/workflows/pytest/badge.svg)
[![PyPI version](https://badge.fury.io/py/alleycat-reactive.svg)](https://badge.fury.io/py/alleycat-reactive)
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

As such, there can be significant changes in the API at any time in future. Furthermore, the project 
may even be discontinued in case the idea it is based upon proves to be an infeasible one.

So, please use it at your discretion and consider opening an issue if you encounter a problem.

## Reactive Object Pattern

AlleyCat Reactive provides an API to implement what we term as _Reactive Object Pattern_ or 
_ROP_ for short. Despite its rather pretentious name, it merely means defining class properties 
which can also serve as an _Observable_ in Rx.

But why do we need such a thing?

We won't delve into this subject too much since you can learn about the concept from many 
other websites.

In short, it's much better to define data in a declarative manner, or as "data pipelines", 
especially when it's changing over time. And Rx is all about composing and manipulating such 
pipelines in a potentially asynchronous context.

But what if the data do not come from an asynchronous source, like Tweets or GUI events, 
but are just properties of an object? Of course, Rx can handle synchronous data as well, but the 
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
a helper function `from_value` as follows:

```python
from alleycat.reactive import RP
from alleycat.reactive import functions as rv

class Toto:

    # Create an instance of ReactiveProperty[int] with an initial value of '99':
    value: RP[int] = rv.from_value(99) # You know the song, don't you? 
```

Note that `RP[T]` is just a convenient alias for `ReactiveProperty[T]` which you can use for 
type hinting. As with other type annotations in Python, it is not strictly necessary. But it 
can be particularly useful when you want to lazily initialize the property.
 
You can declare an 'empty' property using `new_property` and initialize it later as shown 
below. Because it may be difficult to see what type of data the property expects without an 
initial value, using an explicit type annotation can make the code more readable:  

```python
from alleycat.reactive import RP
from alleycat.reactive import functions as rv

class MyClass:

    # Declare an empty property first.
    value: RP[int] = rv.new_property()

    def __init__(self, init_value: int):

        # Then assign a value as you would do to an ordinary property.
        self.value = init_value
```

A `ReactiveProperty` can be can be read and modified like an ordinary class attribute. And 
also you can make it a read-only property by setting the `read_only` argument to `True` like the 
following example:

```python
from alleycat.reactive import RP
from alleycat.reactive import functions as rv

class ArcadiaBay:

    writeable: RP[str] = rv.from_value("life is strange")

    read_only: RP[str] = rv.from_value("the past", read_only=True)


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
from alleycat.reactive import RP
from alleycat.reactive import functions as rv

class Nena:

    ballons: RP[int] = rv.from_value(98)


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

`ReactiveView[T]`(or `RV[T]` for short) is another derivative of `ReactiveValue`, from 
which `ReactiveProperty` is also derived (hence, the alias of `functions` module used 
above, _"rv"_).

The main difference is that while the latter owns a state value itself, a reactive view 
reflects it from an outside source specified as an _Observable_. To create a reactive 
view from an instance of _Observable_, you can use `from_observable` function like this:

```python
import rx
from alleycat.reactive import RV
from alleycat.reactive import functions as rv

class Joni:

    big: RV[str] = rv.from_observable(rx.of("Yellow", "Taxi"))
```

If you are familiar with Rx, you may see it as a wrapper around an _Observable_, while 
a reactive property can be seen as one around a _Subject_.

Like its counterpart, you can initialize a reactive view either eagerly or lazily. In order 
to create a lazy-initializing view, you can use `new_view`, and later provide an _Observable_ 
as shown below:

```python
import rx
from alleycat.reactive import RV
from alleycat.reactive import functions as rv

class BothSides:

    love: RV[str] = rv.new_view()

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
from alleycat.reactive import RP, RV
from alleycat.reactive import functions as rv

class Example:

    value: RP[str] = rv.from_value("Boring!") # I know. But it's not easy to make it interesting, alright?  

    view: RV[str] = value.as_view()
```

### Operators

As we know how to create reactive properties and values, now it's time to learn how to 
transform them. Both variants of `ReactiveValue` provides `map` method, with which you 
can map an arbitrary function or lambda expression over each value in the pipeline:

```python
from alleycat.reactive import RP, RV
from alleycat.reactive import functions as rv

class Counter:

    word: RP[str] = rv.new_property()

    count: RV[str] = word.as_view().map(len).map(lambda o, c: f"The word has {c} letter(s)")
    # The first argument 'o' is the current instance of Counter class.

counter = Counter()

counter.word = "Supercalifragilisticexpialidocious!"

print(counter.count) # Prints "The word has 35 letter(s)". Wait, did you actually count that?
```

You can also use `pipe` to chain arbitrary Rx operators to build a more complex pipeline like this: 

```python
from rx import operators as ops
from alleycat.reactive import RP, RV
from alleycat.reactive import functions as rv

class CrowsCounter:

    animal: RP[str] = rv.new_property()

    # The first argument 'o' is the current instance of Counter class.
    crows: RV[str] = animal.as_view().pipe(lambda o: (
        ops.map(str.lower),
        ops.filter(lambda v: v == "crow"),
        ops.map(lambda _: 1),
        ops.scan(lambda v1, v2: v1 + v2, 0)))

counting = CrowsCounter()

counting.animal = "cat"
counting.animal = "Crow"
counting.animal = "CROW"
counting.animal = "dog"

print(counting.crows) # Returns 2.
```

There are also convenient counterparts to `merge`, `combine_latest`, and `zip` from Rx API, 
which you can use to combine two or more reactive values in a more concise manner:

```python
from alleycat.reactive import RP, RV
from alleycat.reactive import functions as rv

class Rectangle:

    width: RP[int] = rv.from_value(100)

    height: RP[int] = rv.from_value(200)

    area: RV[int] = rv.combine_latest(width, height)(lambda v: v[0] * v[1])

rectangle = Rectangle()

print(rectangle.area) # Prints 20,000... you do the math!

rectangle.width = 150

print(rectangle.area) # Prints 30,000.

rectangle.height = 50

print(rectangle.area) # Prints 750.
```

## Install

The library can be installed using `pip` as follows:
```shell script
pip install alleycat-reactive
```

## License
This project is provided under the terms of _[MIT License](LICENSE)_.
