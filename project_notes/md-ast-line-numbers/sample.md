---
title: YAML-style metadata block
tags: [markdown, ast]
---

+++
title = "Pluses-delimited (TOML-style) metadata block"
+++

# My Heading

My paragraph.

* a
  a
* b
* c

1. d
2. e
3. f

> my block quote

```
my code block
more code block
Even more
```

*emphasis*
**strong**
~~strikethrough~~
[My
 long
  Link](http://example.com)
![My
  long
   Image](http://example.com/image.jpg)

| a | b |
| - | - |
| c | d |
| e | f |

hello[^1]
[^1]: my footnote

## Headings

### ATX level 3 with closing hashes ###

#### ATX level 4

##### ATX level 5

###### ATX level 6

Setext level 1
==============

Setext level 2
--------------

## Heading attributes {#my-id .class1 .class2 key=value flag}

## Paragraphs and breaks

A soft
break, a hard break from two trailing spaces
and a hard break from a backslash\
all in one paragraph.

## Inline syntax

_underscore emphasis_, __underscore strong__, ***strong emphasis***,
`inline code`, `` code containing a ` backtick ``,
\*backslash escapes\*, entities &copy; &#35; &#x22;,
and <span class="x">inline HTML</span><br>.

~~strikethrough~~, ~subscript~, and ^superscript^.

Smart punctuation: "double quotes", 'single quotes', en--dash,
em---dash, and an ellipsis...

## Links and images

[Inline link with title](http://example.com "Link title"),
[full reference][ref], [collapsed reference][], [shortcut reference],
<http://example.com/autolink>, <user@example.com>, and
![reference image][img].

[ref]: http://example.com/ref "Ref title"
[collapsed reference]: http://example.com/collapsed
[shortcut reference]: http://example.com/shortcut
[img]: http://example.com/img.png 'Image title'

## Wikilinks

[[Wiki Page]], [[Wiki Page|custom label]], [[Wiki Page#Section]], and an
embedded image ![[image.png]].

## Lists

3) An ordered list starting at 3
4) using a `)` delimiter

- A loose list

- with nesting:
  1. one
     + deeper
  2. two

* [ ] Task list: unchecked
* [x] checked

## Definition lists

Term 1
: Definition 1

Term 2
: Definition 2a
: Definition 2b

## Block quotes

> Outer quote
> > nested quote
>
> - list in a quote

> [!NOTE]
> GFM note.

> [!TIP]
> GFM tip.

> [!IMPORTANT]
> GFM important.

> [!WARNING]
> GFM warning.

> [!CAUTION]
> GFM caution.

## Code blocks

    indented code block
    second line

```rust
fn main() {
    println!("fenced, with an info string");
}
```

~~~python
print("tilde fence")
~~~

## HTML blocks

<div class="note">
An HTML block.
Even longer.
</div>

<!-- An HTML comment block -->

## Thematic breaks

***

___

- - -

## Tables with alignment

| Left | Center | Right    | None |
| :--- | :----: | -------: | ---- |
| *a*  | `b`    | c \| d   | e    |
| f    | g      | h        | i    |

## Math

Inline math $e^{i\pi} + 1 = 0$ and display math:
$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

## Footnotes

A named footnote[^note].

[^note]: The footnote's text.
