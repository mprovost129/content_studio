from django.http import HttpResponse
from django.views.generic import TemplateView

from studio.services.seo import absolute_url, rss_xml, sitemap_xml, website_schema


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["canonical_url"] = absolute_url("/", request=self.request)
        context["structured_data"] = website_schema(request=self.request)
        return context


def robots_txt(request):
    sitemap_url = absolute_url("/sitemap.xml", request=request)
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /studio/",
            "Disallow: /admin/",
            "Disallow: /accounts/",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap(request):
    return HttpResponse(sitemap_xml(request=request), content_type="application/xml; charset=utf-8")


def feed(request):
    return HttpResponse(rss_xml(request=request), content_type="application/rss+xml; charset=utf-8")
