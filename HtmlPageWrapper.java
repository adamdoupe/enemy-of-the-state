import com.gargoylesoftware.htmlunit.html.HtmlPage;
import com.gargoylesoftware.htmlunit.html.HtmlAnchor;

import java.util.List;
import java.util.ListIterator;

public class HtmlPageWrapper  {
    public HtmlPageWrapper(HtmlPage htmlPage) {
        _htmlPage = htmlPage;
    }

    public HtmlAnchor[] getAnchors() {
        List<HtmlAnchor> anchors = _htmlPage.getAnchors();
        HtmlAnchor[] res = new HtmlAnchor[anchors.size()];
        ListIterator<HtmlAnchor> it = anchors.listIterator();
        for(int i = 0; it.hasNext(); ++i) {
            res[i] = it.next();
        }
        return res;
    }

    public HtmlPage getHtmlPage() {
        return _htmlPage;
    }

    private HtmlPage _htmlPage;
}
