from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
import xml.etree.ElementTree as ET


EXCLUDED_DIRS = {
    "target",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "build",
    "dist",
}

COUNTED_EXTENSIONS = [".java", ".xml", ".jsp", ".properties", ".sql", ".js", ".css"]
TEXT_EXTENSIONS = {
    ".java",
    ".xml",
    ".jsp",
    ".jspx",
    ".properties",
    ".sql",
    ".js",
    ".css",
    ".txt",
    ".md",
    ".yml",
    ".yaml",
}

JAVA_CLASS_TYPES = {
    "Controller": re.compile(r"@Controller\b|class\s+\w*Controller\b"),
    "Service": re.compile(r"@Service\b|interface\s+\w*Service\b|class\s+\w*Service\b"),
    "ServiceImpl": re.compile(r"class\s+\w*ServiceImpl\b"),
    "DAO": re.compile(r"@Repository\b|class\s+\w*DAO\b|class\s+\w*Dao\b"),
    "VO": re.compile(r"class\s+\w*VO\b|class\s+\w*Vo\b"),
    "Mapper": re.compile(r"@Mapper\b|interface\s+\w*Mapper\b|class\s+\w*Mapper\b"),
    "Config": re.compile(r"@Configuration\b|class\s+\w*Config\b"),
}

JAVA_ANNOTATIONS = [
    "@Controller",
    "@Service",
    "@Repository",
    "@Mapper",
    "@Autowired",
    "@Resource",
    "@RequestMapping",
    "@ResponseBody",
    "@Transactional",
]

JAVA_IMPORT_PREFIXES = [
    "egovframework.",
    "org.egovframe.",
    "javax.",
    "jakarta.",
    "com.ibatis.",
    "org.apache.ibatis.",
]

JAVA_EXTENDS_TARGETS = [
    "EgovAbstractDAO",
    "EgovComAbstractDAO",
    "EgovAbstractMapper",
]

JAVA_RISK_PATTERNS = {
    '@SuppressWarnings("unchecked")': re.compile(r'@SuppressWarnings\(\s*"unchecked"\s*\)'),
    "raw Map": re.compile(r"\bMap\s+[A-Za-z_]\w*"),
    "raw List": re.compile(r"\bList\s+[A-Za-z_]\w*"),
    "Vector": re.compile(r"\bVector\b"),
    "Hashtable": re.compile(r"\bHashtable\b"),
    "System.out.println": re.compile(r"\bSystem\.out\.println\s*\("),
    "printStackTrace": re.compile(r"\bprintStackTrace\s*\("),
}

SPRING_XML_FILE_HINTS = (
    "spring",
    "context",
    "servlet",
    "dispatcher",
    "applicationcontext",
)

PROPERTY_KEYWORDS = [
    "datasource",
    "jdbc",
    "url",
    "username",
    "password",
    "driver",
    "crypto",
    "cipher",
    "file",
    "upload",
    "path",
]

SENSITIVE_KEYWORDS = ("password", "passwd", "pwd", "secret", "token")


@dataclass
class ErrorRecord:
    path: str
    reason: str


@dataclass
class ProjectInfo:
    source_root: str
    analyzed_at: str
    total_files: int = 0
    extension_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class MavenInfo:
    pom_exists: bool = False
    project: dict[str, str] = field(default_factory=dict)
    parent: dict[str, str] = field(default_factory=dict)
    properties: dict[str, str] = field(default_factory=dict)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    plugins: list[dict[str, str]] = field(default_factory=list)


@dataclass
class JavaInventory:
    total_files: int = 0
    package_counts: dict[str, int] = field(default_factory=dict)
    class_types: dict[str, int] = field(default_factory=dict)
    annotation_counts: dict[str, int] = field(default_factory=dict)
    import_counts: dict[str, int] = field(default_factory=dict)
    inheritance_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SpringXmlFileInfo:
    path: str
    bean_count: int
    component_scan: bool
    mvc_annotation_driven: bool
    tx_annotation_driven: bool
    datasource_candidates: list[str]
    sql_session_factory_candidates: list[str]
    transaction_manager_candidates: list[str]
    view_resolver_candidates: list[str]


@dataclass
class SpringXmlInventory:
    files: list[SpringXmlFileInfo] = field(default_factory=list)


@dataclass
class SqlMapFileInfo:
    path: str
    statement_count: int
    statement_ids: list[str]


@dataclass
class SqlMapInventory:
    ibatis_files: list[SqlMapFileInfo] = field(default_factory=list)
    mybatis_files: list[SqlMapFileInfo] = field(default_factory=list)
    usage_counts: dict[str, int] = field(default_factory=dict)
    dynamic_tag_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class WebXmlInventory:
    path: str = ""
    servlets: list[str] = field(default_factory=list)
    servlet_mappings: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    listeners: list[str] = field(default_factory=list)
    context_params: list[str] = field(default_factory=list)
    welcome_files: list[str] = field(default_factory=list)
    error_pages: list[str] = field(default_factory=list)


@dataclass
class JspInventory:
    total_files: int = 0
    taglib_counts: dict[str, int] = field(default_factory=dict)
    other_taglibs: dict[str, int] = field(default_factory=dict)
    scriptlet_files: list[str] = field(default_factory=list)
    include_files: list[str] = field(default_factory=list)
    xframe_candidates: list[str] = field(default_factory=list)


@dataclass
class PropertyFileInfo:
    path: str
    keys: list[str]


@dataclass
class PropertiesInventory:
    files: list[PropertyFileInfo] = field(default_factory=list)


@dataclass
class PriorityCandidate:
    priority: int
    area: str
    basis: str
    recommendation: str


@dataclass
class InventoryReport:
    project_info: ProjectInfo
    maven_info: MavenInfo
    java_inventory: JavaInventory
    spring_xml_inventory: SpringXmlInventory
    sql_map_inventory: SqlMapInventory
    web_xml_inventory: WebXmlInventory
    jsp_inventory: JspInventory
    properties_inventory: PropertiesInventory
    priority_candidates: list[PriorityCandidate]
    errors: list[ErrorRecord]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect AS-IS inventory for an eGovFrame project.")
    parser.add_argument("--source-root", required=True, help="Path to the source project root.")
    parser.add_argument("--output", required=True, help="Path to the markdown output file.")
    return parser.parse_args()


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def is_binary_path(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return False
    try:
        with path.open("rb") as file_obj:
            chunk = file_obj.read(4096)
    except OSError:
        return False
    if b"\x00" in chunk:
        return True
    if not chunk:
        return False
    non_text = sum(byte < 9 or (13 < byte < 32) for byte in chunk)
    return (non_text / len(chunk)) > 0.30


def read_text_file(path: Path) -> str:
    encodings = ("utf-8", "cp949")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except OSError as exc:
            last_error = exc
            break
    if last_error is None:
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "unknown decode error")
    raise last_error


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def collect_project_files(source_root: Path, errors: list[ErrorRecord]) -> list[Path]:
    files: list[Path] = []
    for path in source_root.rglob("*"):
        if should_skip(path):
            continue
        if not path.is_file():
            continue
        files.append(path)
    files.sort()
    return files


def build_project_info(source_root: Path, files: list[Path]) -> ProjectInfo:
    counts = {ext: 0 for ext in COUNTED_EXTENSIONS}
    for path in files:
        suffix = path.suffix.lower()
        if suffix in counts:
            counts[suffix] += 1
    return ProjectInfo(
        source_root=str(source_root.resolve()),
        analyzed_at=datetime.now().isoformat(timespec="seconds"),
        total_files=len(files),
        extension_counts=counts,
    )


def resolve_maven_value(raw_value: str, properties: dict[str, str]) -> str:
    value = raw_value.strip()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return properties.get(key, match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replace, value)


def parse_pom(source_root: Path, errors: list[ErrorRecord]) -> MavenInfo:
    pom_path = source_root / "pom.xml"
    if not pom_path.exists():
        return MavenInfo()

    try:
        root = ET.fromstring(read_text_file(pom_path))
    except Exception as exc:
        errors.append(ErrorRecord(relative_path(pom_path, source_root), f"pom.xml parse failed: {exc}"))
        return MavenInfo(pom_exists=True)

    properties: dict[str, str] = {}
    properties_nodes = [child for child in root if local_name(child.tag) == "properties"]
    if properties_nodes:
        for prop in properties_nodes[0]:
            name = local_name(prop.tag)
            properties[name] = (prop.text or "").strip()

    project = {
        "groupId": child_text(root, "groupId"),
        "artifactId": child_text(root, "artifactId"),
        "version": child_text(root, "version"),
        "packaging": child_text(root, "packaging"),
    }

    parent: dict[str, str] = {}
    for child in root:
        if local_name(child.tag) == "parent":
            parent = {
                "groupId": child_text(child, "groupId"),
                "artifactId": child_text(child, "artifactId"),
                "version": child_text(child, "version"),
            }
            break

    if not project["groupId"]:
        project["groupId"] = parent.get("groupId", "")
    if not project["version"]:
        project["version"] = parent.get("version", "")

    dependencies: list[dict[str, str]] = []
    plugins: list[dict[str, str]] = []

    for elem in root.iter():
        name = local_name(elem.tag)
        if name == "dependency":
            dependencies.append(
                {
                    "groupId": resolve_maven_value(child_text(elem, "groupId"), properties),
                    "artifactId": resolve_maven_value(child_text(elem, "artifactId"), properties),
                    "version": resolve_maven_value(child_text(elem, "version"), properties),
                    "scope": resolve_maven_value(child_text(elem, "scope"), properties),
                }
            )
        elif name == "plugin":
            plugins.append(
                {
                    "groupId": resolve_maven_value(child_text(elem, "groupId"), properties),
                    "artifactId": resolve_maven_value(child_text(elem, "artifactId"), properties),
                    "version": resolve_maven_value(child_text(elem, "version"), properties),
                }
            )

    resolved_project = {
        key: resolve_maven_value(value, properties) if value else value
        for key, value in project.items()
    }
    resolved_parent = {
        key: resolve_maven_value(value, properties) if value else value
        for key, value in parent.items()
    }
    resolved_properties = {
        key: resolve_maven_value(value, properties) if value else value
        for key, value in properties.items()
    }

    return MavenInfo(
        pom_exists=True,
        project=resolved_project,
        parent=resolved_parent,
        properties=resolved_properties,
        dependencies=dependencies,
        plugins=plugins,
    )


def classify_java_type(content: str) -> str:
    for class_type, pattern in JAVA_CLASS_TYPES.items():
        if pattern.search(content):
            return class_type
    return "기타"


def collect_java_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> JavaInventory:
    package_counter: Counter[str] = Counter()
    class_type_counter: Counter[str] = Counter()
    annotation_counter: Counter[str] = Counter({key: 0 for key in JAVA_ANNOTATIONS})
    import_counter: Counter[str] = Counter({key: 0 for key in JAVA_IMPORT_PREFIXES})
    inheritance_counter: Counter[str] = Counter({key: 0 for key in JAVA_EXTENDS_TARGETS})
    risk_counter: Counter[str] = Counter({key: 0 for key in JAVA_RISK_PATTERNS})
    java_files = [path for path in files if path.suffix.lower() == ".java"]

    for path in java_files:
        try:
            content = read_text_file(path)
        except Exception as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"java read failed: {exc}"))
            continue

        package_match = re.search(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", content, re.MULTILINE)
        package_name = package_match.group(1) if package_match else "(default)"
        package_counter[package_name] += 1
        class_type_counter[classify_java_type(content)] += 1

        for annotation in JAVA_ANNOTATIONS:
            annotation_counter[annotation] += len(re.findall(re.escape(annotation) + r"\b", content))

        for prefix in JAVA_IMPORT_PREFIXES:
            import_counter[prefix] += len(re.findall(r"^\s*import\s+" + re.escape(prefix), content, re.MULTILINE))

        for target in JAVA_EXTENDS_TARGETS:
            inheritance_counter[target] += len(re.findall(r"\b(?:extends|implements)\s+" + re.escape(target) + r"\b", content))

        for risk_name, pattern in JAVA_RISK_PATTERNS.items():
            risk_counter[risk_name] += len(pattern.findall(content))

    for label in list(JAVA_CLASS_TYPES.keys()) + ["기타"]:
        class_type_counter.setdefault(label, 0)

    return JavaInventory(
        total_files=len(java_files),
        package_counts=dict(sorted(package_counter.items())),
        class_types=dict(class_type_counter),
        annotation_counts=dict(annotation_counter),
        import_counts=dict(import_counter),
        inheritance_counts=dict(inheritance_counter),
        risk_counts=dict(risk_counter),
    )


def is_spring_xml_candidate(path: Path, content: str) -> bool:
    if path.suffix.lower() != ".xml":
        return False
    lowered_path = path.name.lower()
    if any(hint in lowered_path for hint in SPRING_XML_FILE_HINTS):
        return True
    lowered = content.lower()
    return "http://www.springframework.org/schema/beans" in lowered or "<beans" in lowered


def collect_spring_xml_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> SpringXmlInventory:
    result = SpringXmlInventory()
    for path in files:
        if path.suffix.lower() != ".xml":
            continue
        try:
            content = read_text_file(path)
        except Exception as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"xml read failed: {exc}"))
            continue

        if not is_spring_xml_candidate(path, content):
            continue

        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"spring xml parse failed: {exc}"))
            continue

        bean_count = 0
        component_scan = False
        mvc_annotation_driven = False
        tx_annotation_driven = False
        datasource_candidates: list[str] = []
        sql_session_factory_candidates: list[str] = []
        transaction_manager_candidates: list[str] = []
        view_resolver_candidates: list[str] = []

        for elem in root.iter():
            tag_name = local_name(elem.tag)
            elem_id = elem.attrib.get("id") or elem.attrib.get("name") or ""
            class_name = elem.attrib.get("class", "")
            joined = " ".join([elem_id, class_name]).lower()

            if tag_name == "bean":
                bean_count += 1

            if tag_name == "component-scan":
                component_scan = True
            elif tag_name == "annotation-driven" and "mvc" in elem.tag:
                mvc_annotation_driven = True
            elif tag_name == "annotation-driven" and "tx" in elem.tag:
                tx_annotation_driven = True

            if "datasource" in joined or "dataSource" in elem_id:
                datasource_candidates.append(elem_id or class_name or tag_name)
            if "sqlsessionfactory" in joined or "sqlmapsessionfactory" in joined:
                sql_session_factory_candidates.append(elem_id or class_name or tag_name)
            if "transactionmanager" in joined:
                transaction_manager_candidates.append(elem_id or class_name or tag_name)
            if "viewresolver" in joined:
                view_resolver_candidates.append(elem_id or class_name or tag_name)

        result.files.append(
            SpringXmlFileInfo(
                path=relative_path(path, source_root),
                bean_count=bean_count,
                component_scan=component_scan,
                mvc_annotation_driven=mvc_annotation_driven,
                tx_annotation_driven=tx_annotation_driven,
                datasource_candidates=sorted(set(filter(None, datasource_candidates))),
                sql_session_factory_candidates=sorted(set(filter(None, sql_session_factory_candidates))),
                transaction_manager_candidates=sorted(set(filter(None, transaction_manager_candidates))),
                view_resolver_candidates=sorted(set(filter(None, view_resolver_candidates))),
            )
        )

    result.files.sort(key=lambda item: item.path)
    return result


def is_ibatis_sql_map(content: str) -> bool:
    return "<sqlMap" in content or "<sqlmap" in content


def is_mybatis_mapper(content: str) -> bool:
    return bool(re.search(r"<mapper\b[^>]*\bnamespace\s*=", content))


def collect_sql_map_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> SqlMapInventory:
    usage_counter: Counter[str] = Counter({"parameterClass": 0, "resultClass": 0, "resultMap": 0})
    dynamic_counter: Counter[str] = Counter(
        {
            "isEqual": 0,
            "isNotEqual": 0,
            "isEmpty": 0,
            "isNotEmpty": 0,
            "isNull": 0,
            "isNotNull": 0,
            "iterate": 0,
            "dynamic": 0,
        }
    )
    risk_counter: Counter[str] = Counter({"$param$": 0, "#param#": 0, "CDATA": 0})
    ibatis_files: list[SqlMapFileInfo] = []
    mybatis_files: list[SqlMapFileInfo] = []

    for path in files:
        if path.suffix.lower() != ".xml":
            continue
        try:
            content = read_text_file(path)
        except Exception as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"sql xml read failed: {exc}"))
            continue

        if not (is_ibatis_sql_map(content) or is_mybatis_mapper(content)):
            continue

        statement_ids = re.findall(
            r"<(?:select|insert|update|delete|procedure)\b[^>]*\bid\s*=\s*[\"']([^\"']+)[\"']",
            content,
            flags=re.IGNORECASE,
        )
        info = SqlMapFileInfo(
            path=relative_path(path, source_root),
            statement_count=len(statement_ids),
            statement_ids=sorted(statement_ids),
        )

        if is_ibatis_sql_map(content):
            ibatis_files.append(info)
        if is_mybatis_mapper(content):
            mybatis_files.append(info)

        usage_counter["parameterClass"] += len(re.findall(r"\bparameterClass\s*=", content))
        usage_counter["resultClass"] += len(re.findall(r"\bresultClass\s*=", content))
        usage_counter["resultMap"] += len(re.findall(r"\bresultMap\s*=", content))

        for tag_name in dynamic_counter:
            dynamic_counter[tag_name] += len(re.findall(r"<" + re.escape(tag_name) + r"\b", content))

        risk_counter["$param$"] += len(re.findall(r"\$[A-Za-z0-9_.]+\$", content))
        risk_counter["#param#"] += len(re.findall(r"#[A-Za-z0-9_.]+#", content))
        risk_counter["CDATA"] += len(re.findall(r"<!\[CDATA\[", content))

    ibatis_files.sort(key=lambda item: item.path)
    mybatis_files.sort(key=lambda item: item.path)
    return SqlMapInventory(
        ibatis_files=ibatis_files,
        mybatis_files=mybatis_files,
        usage_counts=dict(usage_counter),
        dynamic_tag_counts=dict(dynamic_counter),
        risk_counts=dict(risk_counter),
    )


def collect_web_xml_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> WebXmlInventory:
    web_xml_path = next((path for path in files if path.name.lower() == "web.xml"), None)
    if web_xml_path is None:
        return WebXmlInventory()

    try:
        root = ET.fromstring(read_text_file(web_xml_path))
    except Exception as exc:
        errors.append(ErrorRecord(relative_path(web_xml_path, source_root), f"web.xml parse failed: {exc}"))
        return WebXmlInventory(path=relative_path(web_xml_path, source_root))

    inventory = WebXmlInventory(path=relative_path(web_xml_path, source_root))
    for child in root:
        tag_name = local_name(child.tag)
        if tag_name == "servlet":
            inventory.servlets.append(child_text(child, "servlet-name") or child_text(child, "servlet-class"))
        elif tag_name == "servlet-mapping":
            name = child_text(child, "servlet-name")
            pattern = child_text(child, "url-pattern")
            inventory.servlet_mappings.append(" / ".join(filter(None, [name, pattern])))
        elif tag_name == "filter":
            inventory.filters.append(child_text(child, "filter-name") or child_text(child, "filter-class"))
        elif tag_name == "listener":
            inventory.listeners.append(child_text(child, "listener-class"))
        elif tag_name == "context-param":
            param_name = child_text(child, "param-name")
            inventory.context_params.append(param_name)
        elif tag_name == "welcome-file-list":
            for welcome in child:
                if local_name(welcome.tag) == "welcome-file" and welcome.text:
                    inventory.welcome_files.append(welcome.text.strip())
        elif tag_name == "error-page":
            code = child_text(child, "error-code") or child_text(child, "exception-type")
            location = child_text(child, "location")
            inventory.error_pages.append(" / ".join(filter(None, [code, location])))

    return inventory


def collect_jsp_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> JspInventory:
    inventory = JspInventory(
        taglib_counts={"JSTL": 0, "Spring Form Tag": 0, "기타 Taglib": 0},
    )
    other_taglibs: Counter[str] = Counter()
    jsp_files = [path for path in files if path.suffix.lower() in {".jsp", ".jspx"}]
    inventory.total_files = len(jsp_files)

    for path in jsp_files:
        try:
            content = read_text_file(path)
        except Exception as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"jsp read failed: {exc}"))
            continue

        rel_path = relative_path(path, source_root)
        taglibs = re.findall(r'<%@\s*taglib\s+[^%]*uri\s*=\s*"([^"]+)"', content, flags=re.IGNORECASE)
        for uri in taglibs:
            uri_lower = uri.lower()
            if "java.sun.com/jsp/jstl" in uri_lower or "jakarta.tags" in uri_lower:
                inventory.taglib_counts["JSTL"] += 1
            elif "springframework.org/tags/form" in uri_lower:
                inventory.taglib_counts["Spring Form Tag"] += 1
            else:
                inventory.taglib_counts["기타 Taglib"] += 1
                other_taglibs[uri] += 1

        if re.search(r"<%(?!@|--|=)", content):
            inventory.scriptlet_files.append(rel_path)
        if re.search(r'<%@\s*include\b|<jsp:include\b|<c:import\b', content, flags=re.IGNORECASE):
            inventory.include_files.append(rel_path)
        if re.search(r"xFrame|xframe|XDataSet|xDataSet", content):
            inventory.xframe_candidates.append(rel_path)

    inventory.other_taglibs = dict(sorted(other_taglibs.items()))
    inventory.scriptlet_files.sort()
    inventory.include_files.sort()
    inventory.xframe_candidates.sort()
    return inventory


def mask_property_value(key: str, value: str) -> str:
    lowered = key.lower()
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        return "******"
    return value


def collect_properties_inventory(source_root: Path, files: list[Path], errors: list[ErrorRecord]) -> PropertiesInventory:
    inventory = PropertiesInventory()

    for path in files:
        if path.suffix.lower() != ".properties":
            continue
        try:
            content = read_text_file(path)
        except Exception as exc:
            errors.append(ErrorRecord(relative_path(path, source_root), f"properties read failed: {exc}"))
            continue

        keys: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
            elif ":" in line:
                key, value = line.split(":", 1)
            else:
                continue

            normalized_key = key.strip()
            normalized_value = value.strip()
            if any(keyword in normalized_key.lower() for keyword in PROPERTY_KEYWORDS):
                masked_value = mask_property_value(normalized_key, normalized_value)
                keys.append(f"{normalized_key}={masked_value}")

        inventory.files.append(PropertyFileInfo(path=relative_path(path, source_root), keys=sorted(keys)))

    inventory.files.sort(key=lambda item: item.path)
    return inventory


def generate_priority_candidates(
    maven_info: MavenInfo,
    java_inventory: JavaInventory,
    sql_map_inventory: SqlMapInventory,
    web_xml_inventory: WebXmlInventory,
    jsp_inventory: JspInventory,
) -> list[PriorityCandidate]:
    candidates: list[tuple[str, str, str]] = []

    if sql_map_inventory.ibatis_files:
        candidates.append(("SQL Map", "iBatis sqlMap 존재", "MyBatis Mapper 전환"))
    if java_inventory.inheritance_counts.get("EgovAbstractDAO", 0) > 0:
        candidates.append(("DAO", "EgovAbstractDAO 사용", "DAO 전환 규칙 적용"))
    if java_inventory.inheritance_counts.get("EgovComAbstractDAO", 0) > 0:
        candidates.append(("DAO", "EgovComAbstractDAO 사용", "공통 DAO 전환 규칙 적용"))
    if java_inventory.import_counts.get("egovframework.", 0) > 0:
        candidates.append(("Java Import", "egovframework.rte.* 계열 import 존재", "eGov Runtime 4.3 호환성 검토"))
    if java_inventory.import_counts.get("javax.", 0) > 0 and java_inventory.import_counts.get("jakarta.", 0) > 0:
        candidates.append(("Java Import", "javax.* 와 jakarta.* 혼재", "서블릿/스프링 호환성 위험 점검"))
    if web_xml_inventory.path:
        candidates.append(("web.xml", "web.xml 존재", "Spring Boot 전환 검토"))
    if jsp_inventory.scriptlet_files:
        candidates.append(("JSP", "scriptlet 사용 JSP 존재", "화면 리팩토링 후보 점검"))

    if maven_info.pom_exists:
        for dep in maven_info.dependencies:
            group_id = dep.get("groupId", "")
            artifact_id = dep.get("artifactId", "")
            if "egovframework" in group_id or "egovframework" in artifact_id:
                candidates.insert(0, ("pom.xml", "eGov 3.x dependency 사용", "4.3 dependency 전환 검토"))
                break

    prioritized: list[PriorityCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for area, basis, recommendation in candidates:
        key = (area, basis, recommendation)
        if key in seen:
            continue
        seen.add(key)
        prioritized.append(
            PriorityCandidate(
                priority=len(prioritized) + 1,
                area=area,
                basis=basis,
                recommendation=recommendation,
            )
        )
    return prioritized


def format_kv_lines(items: Iterable[tuple[str, Any]]) -> list[str]:
    lines: list[str] = []
    for key, value in items:
        display = value if value not in ("", None, [], {}) else "없음"
        lines.append(f"- {key}: {display}")
    return lines


def format_simple_list(items: Iterable[str]) -> list[str]:
    values = list(items)
    if not values:
        return ["없음"]
    return [f"- {item}" for item in values]


def format_dict_list(data: dict[str, Any]) -> list[str]:
    if not data:
        return ["없음"]
    lines: list[str] = []
    for key, value in data.items():
        display = value if value not in ("", None, [], {}) else "없음"
        lines.append(f"- {key}: {display}")
    return lines


def render_markdown(report: InventoryReport) -> str:
    lines: list[str] = ["# AS-IS 인벤토리", ""]

    lines.extend(["## 1. 프로젝트 기본 정보", ""])
    lines.extend(
        format_kv_lines(
            [
                ("프로젝트 루트 경로", report.project_info.source_root),
                ("분석 수행 일시", report.project_info.analyzed_at),
                ("전체 파일 수", report.project_info.total_files),
            ]
        )
    )
    lines.append("")
    lines.append("### 확장자별 파일 수")
    lines.extend(format_dict_list(report.project_info.extension_counts))
    lines.append("")

    lines.extend(["## 2. Maven 정보", ""])
    if not report.maven_info.pom_exists:
        lines.append("없음")
    else:
        lines.append("### 프로젝트")
        lines.extend(format_kv_lines(report.maven_info.project.items()))
        lines.append("")
        lines.append("### Parent")
        lines.extend(format_kv_lines(report.maven_info.parent.items()))
        lines.append("")
        lines.append("### Properties")
        lines.extend(format_dict_list(dict(sorted(report.maven_info.properties.items()))))
        lines.append("")
        lines.append("### Dependencies")
        if not report.maven_info.dependencies:
            lines.append("없음")
        else:
            for dep in report.maven_info.dependencies:
                group_id = dep.get("groupId") or "없음"
                artifact_id = dep.get("artifactId") or "없음"
                version = dep.get("version") or "없음"
                scope = dep.get("scope") or "없음"
                lines.append(f"- {group_id}:{artifact_id}:{version} (scope={scope})")
        lines.append("")
        lines.append("### Plugins")
        if not report.maven_info.plugins:
            lines.append("없음")
        else:
            for plugin in report.maven_info.plugins:
                group_id = plugin.get("groupId") or "없음"
                artifact_id = plugin.get("artifactId") or "없음"
                version = plugin.get("version") or "없음"
                lines.append(f"- {group_id}:{artifact_id}:{version}")
    lines.append("")

    lines.extend(["## 3. Java 소스 인벤토리", ""])
    lines.extend(
        format_kv_lines(
            [
                ("전체 Java 파일 수", report.java_inventory.total_files),
            ]
        )
    )
    lines.append("")
    lines.append("### package별 파일 수")
    lines.extend(format_dict_list(report.java_inventory.package_counts))
    lines.append("")
    lines.append("### 클래스 유형 분류")
    lines.extend(format_dict_list(report.java_inventory.class_types))
    lines.append("")
    lines.append("### Annotation 사용 현황")
    lines.extend(format_dict_list(report.java_inventory.annotation_counts))
    lines.append("")
    lines.append("### Import 사용 현황")
    lines.extend(format_dict_list(report.java_inventory.import_counts))
    lines.append("")
    lines.append("### 상속 관계")
    lines.extend(format_dict_list(report.java_inventory.inheritance_counts))
    lines.append("")
    lines.append("### 위험 후보")
    lines.extend(format_dict_list(report.java_inventory.risk_counts))
    lines.append("")

    lines.extend(["## 4. Spring XML 인벤토리", ""])
    if not report.spring_xml_inventory.files:
        lines.append("없음")
    else:
        for item in report.spring_xml_inventory.files:
            lines.append(f"### {item.path}")
            lines.extend(
                format_kv_lines(
                    [
                        ("bean 개수", item.bean_count),
                        ("component-scan 사용 여부", "예" if item.component_scan else "아니오"),
                        ("mvc:annotation-driven 사용 여부", "예" if item.mvc_annotation_driven else "아니오"),
                        ("tx:annotation-driven 사용 여부", "예" if item.tx_annotation_driven else "아니오"),
                        ("datasource 설정 후보", ", ".join(item.datasource_candidates) if item.datasource_candidates else "없음"),
                        (
                            "sqlSessionFactory 설정 후보",
                            ", ".join(item.sql_session_factory_candidates) if item.sql_session_factory_candidates else "없음",
                        ),
                        (
                            "transactionManager 설정 후보",
                            ", ".join(item.transaction_manager_candidates) if item.transaction_manager_candidates else "없음",
                        ),
                        ("viewResolver 설정 후보", ", ".join(item.view_resolver_candidates) if item.view_resolver_candidates else "없음"),
                    ]
                )
            )
            lines.append("")

    lines.extend(["## 5. iBatis / MyBatis SQL Map 인벤토리", ""])
    lines.append("### iBatis SQL Map")
    if not report.sql_map_inventory.ibatis_files:
        lines.append("없음")
    else:
        for item in report.sql_map_inventory.ibatis_files:
            lines.append(f"- {item.path} | statements={item.statement_count} | ids={', '.join(item.statement_ids) if item.statement_ids else '없음'}")
    lines.append("")
    lines.append("### MyBatis Mapper")
    if not report.sql_map_inventory.mybatis_files:
        lines.append("없음")
    else:
        for item in report.sql_map_inventory.mybatis_files:
            lines.append(f"- {item.path} | statements={item.statement_count} | ids={', '.join(item.statement_ids) if item.statement_ids else '없음'}")
    lines.append("")
    lines.append("### 사용 현황")
    lines.extend(format_dict_list(report.sql_map_inventory.usage_counts))
    lines.append("")
    lines.append("### 동적 SQL 태그")
    lines.extend(format_dict_list(report.sql_map_inventory.dynamic_tag_counts))
    lines.append("")
    lines.append("### 위험 패턴")
    lines.extend(format_dict_list(report.sql_map_inventory.risk_counts))
    lines.append("")

    lines.extend(["## 6. Web 설정 인벤토리", ""])
    if not report.web_xml_inventory.path:
        lines.append("없음")
    else:
        lines.extend(
            format_kv_lines(
                [
                    ("파일", report.web_xml_inventory.path),
                ]
            )
        )
        lines.append("")
        lines.append("### servlet")
        lines.extend(format_simple_list(report.web_xml_inventory.servlets))
        lines.append("")
        lines.append("### servlet-mapping")
        lines.extend(format_simple_list(report.web_xml_inventory.servlet_mappings))
        lines.append("")
        lines.append("### filter")
        lines.extend(format_simple_list(report.web_xml_inventory.filters))
        lines.append("")
        lines.append("### listener")
        lines.extend(format_simple_list(report.web_xml_inventory.listeners))
        lines.append("")
        lines.append("### context-param")
        lines.extend(format_simple_list(report.web_xml_inventory.context_params))
        lines.append("")
        lines.append("### welcome-file")
        lines.extend(format_simple_list(report.web_xml_inventory.welcome_files))
        lines.append("")
        lines.append("### error-page")
        lines.extend(format_simple_list(report.web_xml_inventory.error_pages))
    lines.append("")

    lines.extend(["## 7. JSP / 화면 인벤토리", ""])
    lines.extend(format_kv_lines([("JSP 파일 수", report.jsp_inventory.total_files)]))
    lines.append("")
    lines.append("### Taglib 사용 현황")
    lines.extend(format_dict_list(report.jsp_inventory.taglib_counts))
    lines.append("")
    lines.append("### 기타 Taglib")
    lines.extend(format_dict_list(report.jsp_inventory.other_taglibs))
    lines.append("")
    lines.append("### scriptlet 사용 파일")
    lines.extend(format_simple_list(report.jsp_inventory.scriptlet_files))
    lines.append("")
    lines.append("### include 사용 파일")
    lines.extend(format_simple_list(report.jsp_inventory.include_files))
    lines.append("")
    lines.append("### xFrame 후보")
    lines.extend(format_simple_list(report.jsp_inventory.xframe_candidates))
    lines.append("")

    lines.extend(["## 8. Properties 인벤토리", ""])
    if not report.properties_inventory.files:
        lines.append("없음")
    else:
        for item in report.properties_inventory.files:
            lines.append(f"### {item.path}")
            lines.extend(format_simple_list(item.keys))
            lines.append("")

    lines.extend(["## 9. 전환 우선순위 후보", ""])
    if not report.priority_candidates:
        lines.append("없음")
    else:
        lines.append("| 우선순위 | 영역 | 근거 | 권장 작업 |")
        lines.append("| --- | --- | --- | --- |")
        for item in report.priority_candidates:
            lines.append(f"| {item.priority} | {item.area} | {item.basis} | {item.recommendation} |")
    lines.append("")

    lines.extend(["## 10. 분석 오류 파일", ""])
    if not report.errors:
        lines.append("없음")
    else:
        for error in report.errors:
            lines.append(f"- {error.path}: {error.reason}")

    return "\n".join(lines).strip() + "\n"


def collect_inventory(source_root: Path) -> InventoryReport:
    errors: list[ErrorRecord] = []
    files = collect_project_files(source_root, errors)
    filtered_files = [path for path in files if not is_binary_path(path)]

    project_info = build_project_info(source_root, files)
    maven_info = parse_pom(source_root, errors)
    java_inventory = collect_java_inventory(source_root, filtered_files, errors)
    spring_xml_inventory = collect_spring_xml_inventory(source_root, filtered_files, errors)
    sql_map_inventory = collect_sql_map_inventory(source_root, filtered_files, errors)
    web_xml_inventory = collect_web_xml_inventory(source_root, filtered_files, errors)
    jsp_inventory = collect_jsp_inventory(source_root, filtered_files, errors)
    properties_inventory = collect_properties_inventory(source_root, filtered_files, errors)
    priority_candidates = generate_priority_candidates(
        maven_info,
        java_inventory,
        sql_map_inventory,
        web_xml_inventory,
        jsp_inventory,
    )

    return InventoryReport(
        project_info=project_info,
        maven_info=maven_info,
        java_inventory=java_inventory,
        spring_xml_inventory=spring_xml_inventory,
        sql_map_inventory=sql_map_inventory,
        web_xml_inventory=web_xml_inventory,
        jsp_inventory=jsp_inventory,
        properties_inventory=properties_inventory,
        priority_candidates=priority_candidates,
        errors=errors,
    )


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(f"source root is not a directory: {source_root}")

    report = collect_inventory(source_root)
    markdown = render_markdown(report)
    ensure_parent_dir(output_path)
    output_path.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
