//! <h1 id="cc-TB0Jxbo_gu">
//!   <code>main.rs</code> -- Print the event stream (AST) which pulldown-cmark produces
//! </h1>
//!
//! Usage: `md-ast [FILE]`. With no `FILE` (or `-`), read Markdown from stdin.
//!
//! pulldown-cmark doesn't build a tree; it emits a flat stream of events, where
//! each `Start` / `End` pair brackets its children. This program indents each
//! event by its nesting depth so the stream reads as a tree, and prefixes each
//! event with the (1-based) line number in the input where it occurs; since an
//! `End` event spans the same source range as its `Start`, an `End` event's
//! line number is the line where that element ends. `Start` events are printed
//! using the per-tag detail from pulldown-cmark's
//! [parser-map-tag-print](https://github.com/pulldown-cmark/pulldown-cmark/blob/main/pulldown-cmark/examples/parser-map-tag-print.rs)
//! example; all other events use the format from its
//! [parser-map-event-print](https://github.com/pulldown-cmark/pulldown-cmark/blob/main/pulldown-cmark/examples/parser-map-event-print.rs)
//! example.
//!
//! After the AST, the program prints a blank line followed by the HTML which
//! pulldown-cmark renders from the same event stream, with an HTML comment such
//! as `<!--line 3-->` inserted wherever the input line changes (see
//! `add_line_comments` for where these are omitted).

// Imports
// -------
//
// ### Standard library
use std::{
    env, fs,
    io::{self, Read},
    ops::Range,
    process::ExitCode,
};

// ### Third-party
use pulldown_cmark::{CowStr, Event, Options, Parser, Tag, TagEnd, html};

// Code
// ----
fn main() -> ExitCode {
    let markdown_input = match read_input() {
        Ok(s) => s,
        Err(err) => {
            eprintln!("md-ast: {err}");
            return ExitCode::FAILURE;
        }
    };

    // The byte offset at which each line of the input starts.
    let line_starts: Vec<usize> = std::iter::once(0)
        .chain(markdown_input.match_indices('\n').map(|(i, _)| i + 1))
        .collect();
    // Right-align line numbers to the width of the largest one.
    let width = line_starts.len().to_string().len();

    // Collect the events, since they're used twice: once to print the AST, then
    // again to render HTML.
    let events: Vec<_> = Parser::new_ext(&markdown_input, Options::all())
        .into_offset_iter()
        .collect();

    let mut depth = 0;
    for (event, range) in &events {
        // An `End` event's range is the same as its `Start` event's range, so
        // use the last byte of the range to report where the element ends.
        let offset = if let Event::End(_) = event {
            depth -= 1;
            range.end.saturating_sub(1).max(range.start)
        } else {
            range.start
        };
        println!(
            "{:>width$}: {}{}",
            line_number(&line_starts, offset),
            "  ".repeat(depth),
            describe_event(event)
        );
        if let Event::Start(_) = event {
            depth += 1;
        }
    }

    let mut html_output = String::new();
    html::push_html(
        &mut html_output,
        add_line_comments(events, &line_starts).into_iter(),
    );
    println!();
    print!("{html_output}");
    ExitCode::SUCCESS
}

fn read_input(// Returns the Markdown to parse.
) -> io::Result<String> {
    match env::args().nth(1).as_deref() {
        None | Some("-") => {
            let mut s = String::new();
            io::stdin().read_to_string(&mut s)?;
            Ok(s)
        }
        Some(path) => fs::read_to_string(path),
    }
}

fn line_number(
    // The byte offset at which each line starts, as built in `main`.
    line_starts: &[usize],
    // A byte offset into the input.
    offset: usize,
    // Returns the 1-based line number containing `offset`.
) -> usize {
    line_starts.partition_point(|&start| start <= offset)
}

// Insert an HTML comment `<!--line N-->` before the first event which starts on
// each new input line. `End` events are skipped, since their range begins where
// the element starts. A `SoftBreak` or `HardBreak` starts on the line it ends,
// so the comment lands after the break, before the next line's content.
//
// No comments are inserted inside elements where they aren't safe:
//
// * An image: the HTML writer renders everything up to `End(Image)` as the
//   `alt` attribute, so an `InlineHtml` comment would appear there escaped.
// * A raw HTML block: each line is a separate `Html` event, so a comment could
//   land mid-tag, inside a multi-line comment (whose `-->` it would close
//   early), or inside a `<textarea>`, `<script>`, etc.
// * A code block: its `Text` events don't follow line boundaries (CRLF input
//   splits them at each `\r`), and code inside `<code>` may be read via
//   `innerHTML` by a diagram renderer or syntax highlighter.
// * A metadata block: it isn't rendered, but the writer still outputs `Html`
//   events inside it.
//
// One unsafe case remains: a raw `<textarea>`, `<title>`, `<script>` or
// `<style>` tag inside a paragraph which spans lines receives a comment, which
// becomes part of its contents.
fn add_line_comments<'a>(
    // The events and their byte ranges, as produced by `into_offset_iter`.
    events: impl IntoIterator<Item = (Event<'a>, Range<usize>)>,
    // The byte offset at which each line starts, as built in `main`.
    line_starts: &[usize],
    // Returns `events`, minus their ranges, with line-number comments inserted.
) -> Vec<Event<'a>> {
    let mut out = Vec::new();
    let mut last_line = 0;
    // The nesting depth inside elements where a comment isn't safe.
    let mut opaque_depth = 0;
    for (event, range) in events {
        if opaque_depth == 0 && !matches!(event, Event::End(_)) {
            let line = line_number(line_starts, range.start);
            if line != last_line {
                last_line = line;
                out.push(Event::InlineHtml(CowStr::from(format!(
                    "<!--line {line}-->"
                ))));
            }
        }
        match &event {
            Event::Start(
                Tag::Image { .. } | Tag::HtmlBlock | Tag::CodeBlock(_) | Tag::MetadataBlock(_),
            ) => opaque_depth += 1,
            Event::End(
                TagEnd::Image | TagEnd::HtmlBlock | TagEnd::CodeBlock | TagEnd::MetadataBlock(_),
            ) => opaque_depth -= 1,
            _ => {}
        }
        out.push(event);
    }
    out
}

// From `parser-map-event-print.rs`, except that `Start` is expanded using
// `describe_tag`.
fn describe_event(
    event: &Event,
    // Returns a one-line description of `event`.
) -> String {
    match event {
        Event::Start(tag) => format!("Start: {}", describe_tag(tag)),
        Event::End(tag) => format!("End: {:?}", tag),
        Event::Html(s) => format!("Html: {:?}", s),
        Event::InlineHtml(s) => format!("InlineHtml: {:?}", s),
        Event::Text(s) => format!("Text: {:?}", s),
        Event::Code(s) => format!("Code: {:?}", s),
        Event::DisplayMath(s) => format!("DisplayMath: {:?}", s),
        Event::InlineMath(s) => format!("Math: {:?}", s),
        Event::FootnoteReference(s) => format!("FootnoteReference: {:?}", s),
        Event::TaskListMarker(b) => format!("TaskListMarker: {:?}", b),
        Event::SoftBreak => "SoftBreak".to_string(),
        Event::HardBreak => "HardBreak".to_string(),
        Event::Rule => "Rule".to_string(),
    }
}

// From `parser-map-tag-print.rs`, minus `Tag::Highlight` and
// `Tag::ContainerBlock`: those exist only on pulldown-cmark's `main` branch,
// not in the 0.13 release which the CodeChat Editor Server uses.
fn describe_tag(
    tag: &Tag,
    // Returns a one-line description of `tag`.
) -> String {
    match tag {
        Tag::HtmlBlock => "HtmlBlock".to_string(),
        Tag::Heading {
            level,
            id,
            classes,
            attrs,
        } => format!(
            "Heading heading_level: {} fragment identifier: {:?} classes: {:?} attrs: {:?}",
            level, id, classes, attrs
        ),
        Tag::Paragraph => "Paragraph".to_string(),
        Tag::List(ordered_list_first_item_number) => format!(
            "List ordered_list_first_item_number: {:?}",
            ordered_list_first_item_number
        ),
        Tag::DefinitionList => "Definition list".to_string(),
        Tag::DefinitionListTitle => "Definition title (definition list item)".to_string(),
        Tag::DefinitionListDefinition => "Definition (definition list item)".to_string(),
        Tag::Item => "Item (this is a list item)".to_string(),
        Tag::Emphasis => "Emphasis (this is a span tag)".to_string(),
        Tag::Superscript => "Superscript (this is a span tag)".to_string(),
        Tag::Subscript => "Subscript (this is a span tag)".to_string(),
        Tag::Strong => "Strong (this is a span tag)".to_string(),
        Tag::Strikethrough => "Strikethrough (this is a span tag)".to_string(),
        Tag::BlockQuote(kind) => format!("BlockQuote ({:?})", kind),
        Tag::CodeBlock(code_block_kind) => {
            format!("CodeBlock code_block_kind: {:?}", code_block_kind)
        }
        Tag::Link {
            link_type,
            dest_url,
            title,
            id,
        } => format!(
            "Link link_type: {:?} url: {} title: {} id: {}",
            link_type, dest_url, title, id
        ),
        Tag::Image {
            link_type,
            dest_url,
            title,
            id,
        } => format!(
            "Image link_type: {:?} url: {} title: {} id: {}",
            link_type, dest_url, title, id
        ),
        Tag::Table(column_text_alignment_list) => format!(
            "Table column_text_alignment_list: {:?}",
            column_text_alignment_list
        ),
        Tag::TableHead => "TableHead (contains TableRow tags)".to_string(),
        Tag::TableRow => "TableRow (contains TableCell tags)".to_string(),
        Tag::TableCell => "TableCell (contains inline tags)".to_string(),
        Tag::FootnoteDefinition(label) => format!("FootnoteDefinition label: {}", label),
        Tag::MetadataBlock(kind) => format!("MetadataBlock: {:?}", kind),
    }
}
