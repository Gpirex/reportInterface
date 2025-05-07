import importlib

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from domain.utils.format_date import formate_date


def get_page_body(boxes):
    for box in boxes:
        if box.element_tag == 'body':
            return box

        return get_page_body(box.all_children())


async def dynamic_import(module):
    correct_template_import = getattr(
        importlib.import_module(f"domain.templates.{module}.template_config"),
        "report_render_content")

    return correct_template_import


async def report_render(data, report_id):
    report_render_content = await dynamic_import(data['report_template'])

    html = await report_render_content(data)
    main_doc = html.render(stylesheets=[
        CSS("domain/templates/assets/style/reset.css"),
        CSS("domain/templates/assets/style/common.css"),
        CSS("domain/templates/" + data['report_template'] + "/style.css"),
    ])

    exists_links = False

    # Template of header
    env = Environment(loader=FileSystemLoader('.'))
    html = env.get_template("domain/templates/assets/html/header.html")
    template_vars = {
        "report_name": data['report_name']
    }
    html = html.render(template_vars)

    html = HTML(string=html)
    header = html.render(
        stylesheets=[CSS("domain/templates/assets/style/reset.css"),
                     CSS("domain/templates/assets/style/common.css")])

    header_page = header.pages[0]
    exists_links = exists_links or header_page.links
    header_body = get_page_body(header_page._page_box.all_children())
    header_body = header_body.copy_with_children(header_body.all_children())

    generate_date = formate_date(data['generate_date'], "America/Sao_Paulo",
                                 "%m/%d/%Y %H:%M")

    html = env.get_template("domain/templates/assets/html/footer.html")
    template_vars = {
        "generate_date": generate_date
    }
    html = html.render(template_vars)
    html = HTML(string=html)
    footer = html.render(
        stylesheets=[CSS("domain/templates/assets/style/reset.css"),
                     CSS("domain/templates/assets/style/common.css")])

    footer_page = footer.pages[0]
    exists_links = exists_links or footer_page.links

    footer_body = get_page_body(footer_page._page_box.all_children())
    footer_body = footer_body.copy_with_children(footer_body.all_children())

    for i, page in enumerate(main_doc.pages):
        if not i:
            continue

        page_body = get_page_body(page._page_box.all_children())

        page_body.children += header_body.all_children()
        page_body.children += footer_body.all_children()

    try:
        main_doc.write_pdf(
            target=f"reports/report_{data['report_template']}_{report_id}.pdf")
    except IOError as e:
        print(f"Error writing to file: {e}")
