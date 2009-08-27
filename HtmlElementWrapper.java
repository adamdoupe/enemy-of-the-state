import com.gargoylesoftware.htmlunit.html.HtmlElement;

import java.util.List;

public class HtmlElementWrapper  {
    public HtmlElementWrapper(HtmlElement htmlElement) {
        _htmlElement = htmlElement;
    }

    public HtmlElement[] getHtmlElementsByTagName(String name) {
        List<HtmlElement> elements = _htmlElement.getHtmlElementsByTagName(name);
        HtmlElement[] res = new HtmlElement[elements.size()];
        res = elements.toArray(res);
        return res;
    }

    public HtmlElement getHtmlElement() {
        return _htmlElement;
    }

    private HtmlElement _htmlElement;
}

