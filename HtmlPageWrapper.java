import com.gargoylesoftware.htmlunit.html.HtmlPage;
import com.gargoylesoftware.htmlunit.html.HtmlAnchor;
import com.gargoylesoftware.htmlunit.html.HtmlForm;

import java.util.List;
import java.util.ListIterator;

public class HtmlPageWrapper  {
    public HtmlPageWrapper(HtmlPage htmlPage) {
        _htmlPage = htmlPage;
    }

    public HtmlAnchor[] getAnchors() {
        List<HtmlAnchor> anchors = _htmlPage.getAnchors();
        HtmlAnchor[] res = new HtmlAnchor[anchors.size()];
        res = anchors.toArray(res);
        return res;
    }

    public HtmlForm[] getForms() {
        List<HtmlForm> forms = _htmlPage.getForms();
        HtmlForm[] res = new HtmlForm[forms.size()];
        res = forms.toArray(res);
        return res;
    }

    public HtmlPage getHtmlPage() {
        return _htmlPage;
    }

    private HtmlPage _htmlPage;
}
