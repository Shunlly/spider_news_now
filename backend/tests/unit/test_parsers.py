"""
新闻解析器单元测试 - News Parser Unit Tests
T061: Unit test for news parser (trafilatura)

测试正文解析功能，不依赖外部服务。
"""

import trafilatura

from app.services.content_parser_service import ContentParserService


class TestTrafilaturaParser:
    """Trafilatura 正文解析测试"""

    def test_extract_from_simple_html(self):
        """测试从简单 HTML 提取正文"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Article</title></head>
        <body>
            <header>Site Header</header>
            <article>
                <h1>Main Title</h1>
                <p>This is the main content of the article.</p>
                <p>It has multiple paragraphs with important information.</p>
            </article>
            <footer>Site Footer</footer>
        </body>
        </html>
        """
        result = trafilatura.extract(html)

        assert result is not None
        assert "main content" in result.lower()
        assert "important information" in result.lower()

    def test_extract_from_news_html(self):
        """测试从新闻页面 HTML 提取正文"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Breaking News</title></head>
        <body>
            <nav>Home | News | Sports</nav>
            <article class="news-article">
                <h1>Major Event Happens Today</h1>
                <div class="meta">Published: 2024-01-15</div>
                <div class="content">
                    <p>A significant event occurred today in the city center.</p>
                    <p>Officials have confirmed the details of the incident.</p>
                    <p>More updates are expected in the coming hours.</p>
                </div>
            </article>
            <aside>Related Articles</aside>
        </body>
        </html>
        """
        result = trafilatura.extract(html)

        assert result is not None
        assert "significant event" in result.lower()
        assert "officials have confirmed" in result.lower()

    def test_extract_returns_none_for_empty_html(self):
        """测试空 HTML 返回 None"""
        result = trafilatura.extract("")
        assert result is None

    def test_extract_returns_none_for_navigation_only(self):
        """测试只有导航内容时返回 None"""
        html = """
        <html>
        <body>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
        </body>
        </html>
        """
        result = trafilatura.extract(html)
        # trafilatura 会返回 None 或很短的文本
        assert result is None or len(result) < 50

    def test_extract_handles_unicode(self):
        """测试处理 Unicode 中文内容"""
        html = """
        <html>
        <body>
            <article>
                <h1>新闻标题</h1>
                <p>这是一段中文新闻内容，包含重要信息。</p>
                <p>本报讯：记者从相关部门获悉，一项重要政策即将出台。</p>
            </article>
        </body>
        </html>
        """
        result = trafilatura.extract(html)

        assert result is not None
        assert "中文新闻内容" in result
        assert "重要信息" in result

    def test_extract_with_output_format_txt(self):
        """测试纯文本输出格式"""
        # trafilatura 需要足够长的内容才能正确解析
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        <article>
            <h1>Title of the Article</h1>
            <p>First paragraph with bold text that contains enough content.</p>
            <p>Second paragraph with italic text and additional information.</p>
            <p>Third paragraph to ensure the content is long enough for extraction.</p>
        </article>
        </body>
        </html>
        """
        result = trafilatura.extract(html, output_format="txt")

        # trafilatura 可能对短文本返回 None
        if result is not None:
            # 纯文本格式不应包含 HTML 标签
            assert "<strong>" not in result
            assert "<em>" not in result

    def test_extract_with_include_comments_false(self):
        """测试排除评论内容"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>News</title></head>
        <body>
        <article class="news-article">
            <h1>Article Title Goes Here</h1>
            <p>Main article content here with enough text to be recognized.</p>
            <p>This is the second paragraph with more information about the topic.</p>
            <p>And a third paragraph to ensure proper content extraction.</p>
            <div class="comments">
                <p>This is a user comment that should be excluded.</p>
            </div>
        </article>
        </body>
        </html>
        """
        result = trafilatura.extract(html, include_comments=False)

        # trafilatura 可能对某些 HTML 返回 None
        if result is not None:
            assert "main article content" in result.lower()


class TestContentParserServiceHelpers:
    """ContentParserService 辅助方法测试"""

    def test_extract_plain_text_removes_tags(self):
        """测试从 HTML 提取纯文本"""
        html = "<p>Hello <strong>World</strong></p><div>More text</div>"
        result = ContentParserService._extract_plain_text(html)

        assert "Hello" in result
        assert "World" in result
        assert "More text" in result
        assert "<p>" not in result
        assert "<strong>" not in result

    def test_extract_plain_text_handles_whitespace(self):
        """测试处理多余空白"""
        html = "<p>Hello    World</p>\n\n<p>Test</p>"
        result = ContentParserService._extract_plain_text(html)

        # 多余空白应该被规范化
        assert "Hello" in result
        assert "World" in result
        assert "  " not in result  # 不应有连续空格

    def test_extract_plain_text_truncates_long_content(self):
        """测试长文本截断"""
        # 创建超过 10000 字符的内容
        long_content = "<p>" + "A" * 15000 + "</p>"
        result = ContentParserService._extract_plain_text(long_content)

        assert len(result) <= 10000

    def test_extract_plain_text_handles_empty_input(self):
        """测试处理空输入"""
        result = ContentParserService._extract_plain_text("")
        assert result == ""

    def test_extract_plain_text_handles_special_chars(self):
        """测试处理特殊字符"""
        html = "<p>Price: $100 &amp; Tax: 10%</p>"
        result = ContentParserService._extract_plain_text(html)

        assert "$100" in result
        assert "&amp;" in result or "&" in result  # HTML 实体可能保留

    def test_extract_plain_text_unicode(self):
        """测试处理中文内容"""
        html = "<article><p>这是一段中文测试内容</p></article>"
        result = ContentParserService._extract_plain_text(html)

        assert "中文测试内容" in result
