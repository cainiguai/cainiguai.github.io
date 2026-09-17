import unittest
from html.parser import HTMLParser
from pathlib import Path


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []
        self.text_parts = []

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    @property
    def text(self):
        return "".join(self.text_parts + [child.text for child in self.children]).strip()

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()


class PageParser(HTMLParser):
    void_tags = {"meta", "link", "img", "br", "hr", "input"}

    def __init__(self):
        super().__init__()
        self.root = Node("document", [])
        self.stack = [self.root]
        self.styles = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag == "style":
            self._in_style = True
        if tag not in self.void_tags:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        elif self.stack:
            self.stack[-1].text_parts.append(data)


def nodes(root, *, tag=None, node_id=None, class_name=None):
    result = []
    for node in [root, *root.descendants()]:
        if tag and node.tag != tag:
            continue
        if node_id and node.attrs.get("id") != node_id:
            continue
        if class_name and class_name not in node.classes:
            continue
        result.append(node)
    return result


def first(root, **criteria):
    matches = nodes(root, **criteria)
    return matches[0] if matches else None


class UniversalProfilePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (Path(__file__).parents[1] / "index.html").read_text(encoding="utf-8")
        cls.parser = PageParser()
        cls.parser.feed(html)
        cls.root = cls.parser.root
        cls.css = "\n".join(cls.parser.styles)
        cls.visible_text = cls.root.text

    def test_public_profile_has_general_positioning_and_safe_contact(self):
        hero = first(self.root, tag="section", node_id="top")
        self.assertIsNotNone(hero)
        self.assertIn("周碧漪", hero.text)
        self.assertIn("产业研究 · 经营分析 · 项目协同", hero.text)

        email = next(
            (link for link in nodes(self.root, tag="a") if link.attrs.get("href") == "mailto:15990274205@163.com"),
            None,
        )
        self.assertIsNotNone(email)
        self.assertFalse(any(link.attrs.get("href", "").startswith("tel:") for link in nodes(self.root, tag="a")))
        for private_label in ("24岁", "汉族", "中共党员", "基本信息："):
            self.assertNotIn(private_label, self.visible_text)

    def test_main_sections_follow_the_approved_general_order(self):
        main = first(self.root, tag="main")
        section_ids = [child.attrs.get("id") for child in main.children if child.tag == "section"]
        self.assertEqual(
            section_ids,
            ["top", "education", "awards", "skills", "experience", "projects", "leadership"],
        )

    def test_project_portfolio_covers_research_ai_business_and_early_practice(self):
        projects = first(self.root, tag="section", node_id="projects")
        self.assertIsNotNone(projects)
        cards = nodes(projects, tag="article", class_name="project-card")
        self.assertEqual(len(cards), 7)
        project_text = projects.text
        featured = first(projects, tag="article", class_name="featured")
        self.assertIn("能源财税方向课题组", featured.text)
        self.assertIn("科研助理", featured.text)
        self.assertIn("新能源示范城市", project_text)
        self.assertIn("双重差分法", featured.text)
        self.assertIn("Sustainability", featured.text)
        self.assertIn("第二作者", featured.text)
        self.assertIn("SCI/SSCI", project_text)
        self.assertIn("ArcGIS", project_text)
        self.assertIn("《中国宏观经济学》", project_text)
        self.assertIn("AI 个人简历网站创作实践", project_text)
        self.assertIn("2026.08—2026.09", project_text)
        self.assertIn("简约展示版", project_text)
        self.assertIn("3D 交互版", project_text)
        self.assertIn("言出法随——AI-OPC 超级工作流", project_text)
        self.assertIn("2026.02—2026.06", project_text)
        self.assertIn("守护金陵文脉", project_text)
        self.assertIn("基于物联网的智能社区建设新探索", project_text)
        self.assertIn("2022.09—2023.05", project_text)
        self.assertIn("有效问卷 300+ 份", project_text)
        self.assertIn("省赛答辩成绩位列前 10%", project_text)
        self.assertIn("向北开放背景下黑龙江自贸区发展路径研究", project_text)
        self.assertIn("5 个沿边自贸区", project_text)
        self.assertIn("探寻红船精神，担当时代使命", project_text)

        expected_links = {
            "https://www.mdpi.com/2071-1050/17/19/8603",
            "https://cainiguai.github.io/",
            "https://app-e1fdo6486jgh.miaoda.online",
        }
        project_links = {
            link.attrs.get("href")
            for link in nodes(projects, tag="a")
            if link.attrs.get("href") in expected_links
        }
        self.assertEqual(project_links, expected_links)

    def test_latest_resume_updates_education_experience_and_capabilities(self):
        education = first(self.root, tag="section", node_id="education")
        cards = nodes(education, tag="article", class_name="card")
        masters = next(card for card in cards if "北京工商大学" in card.text)
        bachelors = next(card for card in cards if "黑龙江大学" in card.text)
        self.assertIn("GPA 4.22/5.0", masters.text)
        self.assertIn("前 5%", masters.text)
        self.assertIn("GPA 9.0/10.0", bachelors.text)
        self.assertIn("推免资格", bachelors.text)

        experience = first(self.root, tag="section", node_id="experience")
        self.assertIn("京东世纪贸易有限公司", experience.text)
        self.assertIn("采销助理", experience.text)
        self.assertIn("2025.05—2025.08", experience.text)
        self.assertIn("8 个样板间", experience.text)
        self.assertIn("船舶行业", experience.text)
        self.assertIn("中青报视频会议方案", experience.text)

        skills = first(self.root, tag="section", node_id="skills")
        self.assertIn("ArcGIS", skills.text)
        self.assertIn("学术论文写作", skills.text)
        self.assertIn("英文文献阅读", skills.text)

        awards = first(self.root, tag="section", node_id="awards")
        for honor in ("中研杯国赛一等奖", "优秀党员", "一等奖学金", "Sustainability", "第二作者"):
            self.assertIn(honor, awards.text)

        leadership = first(self.root, tag="section", node_id="leadership")
        self.assertIn("12 名积极分子及 3 名党员", leadership.text)
        self.assertIn("2024.09—2027.06", leadership.text)
        self.assertIn("5/34", leadership.text)

    def test_latest_resume_additions_preserve_public_privacy_boundary(self):
        self.assertEqual(nodes(self.root, tag="img"), [])
        for private_value in ("159-9027-4205", "24岁", "女 |", "中共党员"):
            self.assertNotIn(private_value, self.visible_text)

    def test_five_experiences_have_scannable_evidence_bullets(self):
        experience = first(self.root, tag="section", node_id="experience")
        roles = nodes(experience, tag="article", class_name="role")
        self.assertEqual(len(roles), 5)
        for role in roles:
            detail_list = first(role, tag="ul", class_name="detail-list")
            self.assertIsNotNone(detail_list)
            bullet_count = len([child for child in detail_list.children if child.tag == "li"])
            self.assertGreaterEqual(bullet_count, 2)
            self.assertLessEqual(bullet_count, 3)

    def test_hero_surfaces_evidence_based_personal_keywords(self):
        hero = first(self.root, tag="section", node_id="top")
        self.assertIn("Top 5%", hero.text)
        self.assertIn("个人关键词", hero.text)
        for keyword in ("数据分析", "用户洞察", "经营增长", "产业研究", "项目统筹", "AI 提效"):
            self.assertIn(keyword, hero.text)

    def test_awards_are_grouped_for_fast_scanning(self):
        awards = first(self.root, tag="section", node_id="awards")
        groups = nodes(awards, tag="article", class_name="award-group")
        self.assertEqual(len(groups), 2)
        self.assertIn("省级及以上", awards.text)
        self.assertIn("奖学金与校级荣誉", awards.text)

    def test_experience_and_leadership_keep_full_evidence(self):
        experience = first(self.root, tag="section", node_id="experience")
        for phrase in ("类目及渠道对比", "订单来源", "合规性", "船舶行业"):
            self.assertIn(phrase, experience.text)
        self.assertIn("宁波市象山县发改局", experience.text)
        self.assertNotIn("宁波市象山县发改局、团县委", experience.text)
        self.assertNotIn("未来规划", experience.text)

        leadership = first(self.root, tag="section", node_id="leadership")
        cards = nodes(leadership, tag="article", class_name="leadership-card")
        self.assertEqual(len(cards), 2)
        for card in cards:
            keywords = first(card, tag="ul", class_name="keywords")
            details = first(card, tag="ul", class_name="detail-list")
            self.assertIsNotNone(keywords)
            self.assertIsNotNone(details)
            self.assertGreaterEqual(len([child for child in details.children if child.tag == "li"]), 3)

    def test_awards_and_mobile_summary_stay_compact(self):
        self.assertIn(".award-board{display:grid;grid-template-columns:1.15fr .85fr;gap:18px;align-items:start}", self.css)
        self.assertIn(".summary{grid-template-columns:repeat(2,1fr)", self.css)
        self.assertIn(".summary p{font-size:12px}", self.css)

    def test_early_practice_card_has_a_visible_surface_and_frame(self):
        self.assertIn(
            ".project-card.compact{background:var(--paper);border-color:#bfc9c9}",
            self.css,
        )

    def test_static_professional_theme_has_no_ocean_animation(self):
        self.assertEqual(nodes(self.root, class_name="ocean-scene"), [])
        self.assertNotIn("@keyframes", self.css)
        self.assertNotIn("animation:", self.css)

    def test_navigation_links_resolve_to_page_sections(self):
        ids = {node.attrs["id"] for node in self.root.descendants() if "id" in node.attrs}
        nav = first(self.root, tag="nav")
        for link in nodes(nav, tag="a"):
            href = link.attrs.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], ids)


if __name__ == "__main__":
    unittest.main()
