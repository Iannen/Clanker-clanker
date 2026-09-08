# Indentation Fight Club --- GitHub README `<details>` contenders

If the goal is **visually centered / indented collapsible content
without making the `<summary>` a bullet**, there is an important
constraint:

> GitHub's Markdown renderer does not give `<details>` a native "indent
> this whole block" control.

So the contenders below are mostly tricks involving HTML containers,
blockquotes, tables, or CSS-like markup. GitHub strips or ignores some
HTML/CSS, so I've marked the likely reliability.

------------------------------------------------------------------------

## 0. Baseline: plain `<details>`

**Reliability:** ★★★★★\
**Appearance:** left aligned

``` html
<details>
<summary>What I have now</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

```{=html}
</details>
```

    This is the cleanest GitHub-native option, but it does not solve the indentation problem.

    ---

    # Contenders

    ## 1. Put the whole `<details>` inside a blockquote

    **Reliability:** ★★★★★  
    **Appearance:** indented with the normal GitHub quote gutter

    ```markdown
    > <details>
    > <summary>Indented details</summary>
    >
    > ```python
    > def hello():
    >     print("Hello, World!")
    >     return True
    > ```
    >
    > </details>

### Why it is worth trying

This is probably the first contender I would test. The `<details>`
itself is inside the blockquote, so the entire component gets pushed
right without putting a bullet in front of the summary.

### Downside

The indentation is specifically **blockquote indentation**, so you get
the quote styling/gutter. It is not arbitrary horizontal padding.

------------------------------------------------------------------------

## 2. Blockquote the opening/closing tags, but not the code

**Reliability:** ★★★\
**Appearance:** potentially awkward

``` markdown
> <details>
> <summary>Indented details</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

> ```{=html}
> </details>
> ```


    ### Verdict

    Usually not worth it. Markdown's block structure gets involved, and the code block may no longer behave as a child of `<details>` in the way you want.

    **Contender status: experimental.**

    ---

    ## 3. Use a one-cell HTML table as an indentation wrapper

    **Reliability:** ★★★★  
    **Appearance:** often surprisingly good

    ```html
    <table>
    <tr>
    <td>

    <details>
    <summary>Indented details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```

    ### Why this is interesting

    A table cell naturally creates horizontal inset. Unlike a list, it does not introduce a bullet.

    ### Downside

    It is semantically a table being used for layout. Also, GitHub's handling of Markdown inside HTML/table structures can occasionally be finicky.

    **Contender status: strong hack.**

    ---

    ## 4. Use an HTML `<div>` wrapper

    **Reliability:** ★★★★  
    **Appearance:** depends on what GitHub permits

    ```html
    <div align="center">

    <details>
    <summary>Centered details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</div>
```

    ### Important distinction

    `align="center"` is useful if what you actually want is **centering**, rather than merely indentation.

    It is much cleaner than trying to put spaces into `<summary>`.

    ### Downside

    This centers the content rather than providing a controlled left margin.

    **Contender status: good if "centered" is really the goal.**

    ---

    ## 5. `<div align="center">` around only the `<details>`

    ```html
    <div align="center">
    <details>
    <summary>Centered details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</div>
```

    **Reliability:** ★★★★  
    **Use when:** you want the collapsible itself centered.

    This is essentially the compact version of contender #4.

    ---

    ## 6. Try the obsolete-but-often-rendered `<center>` element

    **Reliability:** ★★★  
    **Appearance:** centered

    ```html
    <center>
    <details>
    <summary>Centered details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</center>
```

    ### Verdict

    It can work as a GitHub README hack, but `<center>` is obsolete HTML. If you're building a README you expect to maintain for years, `align="center"` is preferable.

    ---

    ## 7. Fake a margin with an HTML table

    If you want **indentation rather than centering**, a table can be made deliberately asymmetric:

    ```html
    <table>
    <tr>
    <td width="10%"></td>
    <td width="90%">

    <details>
    <summary>Indented details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```

    ### Why this is interesting

    The empty first cell acts as your left margin.

    You can experiment with:

    ```html
    <td width="5%"></td>
    <td width="95%">

or:

``` html
<td width="15%"></td>
<td width="85%">
```

### Verdict

**One of the strongest contenders if you specifically want a visible
left offset.**

------------------------------------------------------------------------

## 8. Use a table with a blank spacer column

A slightly more explicit variant:

``` html
<table>
<tr>
<td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
<td>

<details>
<summary>Indented details</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```

    **Reliability:** ★★★  
    **Downside:** spaces/`&nbsp;` are a crude measuring instrument.

    Prefer percentage widths if the README needs to survive different screen sizes.

    ---

    ## 9. Nested blockquotes

    If you want a *deeper* indentation:

    ```markdown
    > > <details>
    > > <summary>Deeply indented details</summary>
    > >
    > > ```python
    > > def hello():
    > >     print("Hello, World!")
    > >     return True
    > > ```
    > >
    > > </details>

**Reliability:** ★★★★★\
**Appearance:** deeply nested quote

This is ugly but useful as a diagnostic: if one level is too subtle,
multiple levels prove that the `<details>` can be shifted as a Markdown
block.

**Downside:** obviously looks like a blockquote.

------------------------------------------------------------------------

## 10. Put `<details>` inside a list item, then suppress the visual bullet with HTML

``` html
<ul>
<li style="list-style: none;">

<details>
<summary>Indented details</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

```{=html}
</details>
```
```{=html}
</li>
```
```{=html}
</ul>
```

    ### The catch

    GitHub sanitizes HTML and CSS. In particular, you should **not count on arbitrary inline CSS surviving/rendering as expected**.

    So although this is conceptually elegant, it is not a dependable GitHub README solution.

    **Contender status: fun experiment, not my recommendation.**

    ---

    ## 11. `<dl>` / definition-list wrapper

    Another semantic-ish HTML hack:

    ```html
    <dl>
    <dt>

    <details>
    <summary>Indented details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</dt>
```
```{=html}
</dl>
```

    **Reliability:** ★★  
    **Verdict:** interesting, but too renderer-dependent to recommend.

    ---

    ## 12. Use a nested HTML `<blockquote>` explicitly

    Instead of Markdown's `>` syntax:

    ```html
    <blockquote>

    <details>
    <summary>Indented details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</blockquote>
```

    **Reliability:** ★★★★  
    **Appearance:** same basic idea as a Markdown blockquote

    This is useful if you want the indentation wrapper to be visually separated from the surrounding Markdown.

    ---

    ## 13. `<details>` inside a `<div>`, with HTML alignment

    ```html
    <div align="right">

    <details>
    <summary>Right-aligned details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</div>
```

    You can test:

    ```html
    <div align="left">

``` html
<div align="center">
```

``` html
<div align="right">
```

**Reliability:** ★★★★

This gives you alignment, but not arbitrary padding.

------------------------------------------------------------------------

## 14. Center the summary, leave the code alone

Sometimes the actual readability problem is the **summary**, not the
code.

``` html
<details>
<summary align="center">What is inside this?</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

```{=html}
</details>
```

    **Reliability:** ★★★  
    **Verdict:** worth testing, but browser/GitHub handling of attributes on `<summary>` is less compelling than using an outer wrapper.

    ---

    ## 15. Center everything with a table

    ```html
    <table align="center">
    <tr>
    <td>

    <details>
    <summary>Centered details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```

    **Reliability:** ★★★★  

    This combines two tricks: a table gives you a layout container, and `align="center"` positions it.

    ---

    ## 16. Use a fixed-width-ish spacer table

    For a very deliberate "README layout" aesthetic:

    ```html
    <table>
    <tr>
    <td width="20%"></td>
    <td width="60%">

    <details>
    <summary>Details</summary>

    ```python
    def hello():
        print("Hello, World!")
        return True

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
<td width="20%">
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```

    ### Result

    The details block occupies roughly the middle 60% of the page.

    **Reliability:** ★★★★  
    **Use when:** you want a visually constrained README rather than merely a little indentation.

    ---

    # Things I would NOT bother fighting

    ## A. Leading spaces inside `<summary>`

    ```html
    <summary>        summary</summary>

This is not a reliable way to create layout whitespace. HTML collapses
ordinary whitespace.

You can technically use entities such as:

``` html
<summary>&nbsp;&nbsp;&nbsp;summary</summary>
```

but that's manually painting whitespace into your label rather than
moving the component.

**Verdict: no.**

------------------------------------------------------------------------

## B. CSS `margin-left`

The theoretically obvious solution:

``` html
<details style="margin-left: 40px;">
```

or:

``` html
<div style="margin-left: 40px;">
```

would be ideal in unrestricted HTML.

But GitHub sanitizes README HTML, and you should not design your README
around arbitrary CSS being honored.

**Verdict: don't build the README around it.**

------------------------------------------------------------------------

## C. `<details style="padding-left: ...">`

Same problem.

``` html
<details style="padding-left: 50px;">
```

Looks like the perfect answer in a normal webpage.

For GitHub README Markdown, however, **CSS support is not a dependable
layout mechanism**.

------------------------------------------------------------------------

## D. A Markdown list solely for indentation

``` markdown
- <details>
  <summary>...</summary>
```

Yes, it gives you indentation.

But you already identified the problem: you don't want your collapsible
to visually become a list item.

**Verdict: technically effective, aesthetically wrong.**

------------------------------------------------------------------------

# My shortlist

If I were optimizing a GitHub README, I'd test these in this order:

### 🥇 1. Blockquote wrapper

``` markdown
> <details>
> <summary>Something</summary>
>
> ...
>
> </details>
```

**Best native-ish solution.** No fake whitespace and no bullet.

------------------------------------------------------------------------

### 🥈 2. Asymmetric table

``` html
<table>
<tr>
<td width="10%"></td>
<td width="90%">

<details>
<summary>Something</summary>

...
</details>

</td>
</tr>
</table>
```

**Best actual indentation hack.** It gives you a controllable left
offset without a bullet.

------------------------------------------------------------------------

### 🥉 3. Centering wrapper

``` html
<div align="center">

<details>
<summary>Something</summary>

...
</details>

</div>
```

**Best if you mean "center this component" rather than "indent it."**

------------------------------------------------------------------------

### 4. Centered table

``` html
<table align="center">
<tr>
<td>

<details>
<summary>Something</summary>

...
</details>

</td>
</tr>
</table>
```

A nice alternative if the `<div align="center">` rendering isn't giving
you the visual result you want.

------------------------------------------------------------------------

# One important Markdown gotcha

When mixing raw HTML and fenced Markdown code blocks, **blank lines
matter**.

For example, prefer:

``` html
<details>
<summary>Example</summary>

```python
def hello():
    print("Hello, World!")
```

```{=html}
</details>
```

    rather than trying to cram everything together:

    ```html
    <details><summary>Example</summary>
    ```python
    def hello():
        print("Hello, World!")

```{=html}
</details>
```

    GitHub's Markdown parser has special interactions between raw HTML blocks and Markdown. Keeping the code fence separated by blank lines generally makes the intent much clearer and the rendering more predictable.

    ---

    # Final recommendation

    If your desired visual is approximately:

    ```text
    README text
    README text

              ▸ My collapsible
                ┌───────────────────────┐
                │ def hello():          │
                │     print(...)        │
                │     return True        │
                └───────────────────────┘

    README text

then **the asymmetric table hack is the contender I'd investigate
first**:

``` html
<table>
<tr>
<td width="10%"></td>
<td width="90%">

<details>
<summary>▸ My collapsible</summary>

```python
def hello():
    print("Hello, World!")
    return True
```

```{=html}
</details>
```
```{=html}
</td>
```
```{=html}
</tr>
```
```{=html}
</table>
```
\`\`\`

It avoids the three things you seem to dislike:

1.  no bullet;
2.  no fake spaces in the summary;
3.  no dependency on arbitrary CSS.

The trade-off is that you're using an HTML table as a layout primitive,
so whether that is worth it depends on how "hacky" you're willing to let
the README become.

------------------------------------------------------------------------

# Quick test matrix

  Technique                   Indentation   No bullet   GitHub-friendly My verdict
  ------------------------- ------------- ----------- ----------------- -------------------------
  Plain `<details>`                    ❌          ✅                ✅ Baseline
  Spaces in `<summary>`                ⚠️          ✅                ✅ Avoid
  `&nbsp;` in `<summary>`              ⚠️          ✅                ✅ Hacky
  Blockquote                           ✅          ✅                ✅ **Strong**
  Nested blockquote                  ✅✅          ✅                ✅ Ugly but works
  `<div align="center">`           Center          ✅             ✅/⚠️ **Strong**
  `<blockquote>`                       ✅          ✅             ✅/⚠️ Strong
  One-cell table                       ✅          ✅             ✅/⚠️ **Strong**
  Asymmetric table                   ✅✅          ✅             ✅/⚠️ **Best hack**
  `style="margin-left"`                ✅          ✅                ⚠️ Avoid
  `style="padding-left"`               ✅          ✅                ⚠️ Avoid
  List item                            ✅          ❌                ✅ You already rejected it
  `<center>`                       Center          ✅                ⚠️ Legacy hack
  `<dl>`                               ⚠️          ✅                ⚠️ Experimental
