"""共享常量和工具函数 - 避免每个API模块重复定义"""
from app.services.encryption_service import encryption_service as _enc

# 加密服务单例（直接import，避免每次调用get_encryption_service()）
enc = _enc

# 陵水县机构编码→名称映射（全局唯一，避免每个API重复定义）
ORG_NAME_MAP = {
    # 市县级 (8位)
    "460123": "陵水县",
    # 乡镇级 (9位)
    "46012301": "陵水县人民医院",
    "46012302": "椰林镇卫生院",
    "46012303": "椰林镇卫生院",
    "46012304": "三才镇卫生院",
    "46012305": "三才镇卫生院",
    "46012306": "英州镇卫生院",
    "46012307": "本号镇卫生院",
    "46012308": "隆广镇卫生院",
    "46012309": "新村镇卫生院",
    "46012310": "黎安镇卫生院",
    "460123011": "文罗镇卫生院",
    "460123012": "群英乡卫生院",
    "460123013": "提蒙乡卫生院",
    # 村级/其他 (10位+)
    "460123001": "陵水县中医院",
}

# 慢病类型英文→中文映射
DISEASE_NAME_MAP = {
    "HYPERTENSION": "高血压",
    "DIABETES": "糖尿病",
    "CORONARY": "冠心病",
    "STROKE": "脑卒中",
    "COPD": "慢阻肺",
    "CKD": "慢性肾病",
}


def decrypt_patient_name(patient) -> str:
    """解密患者姓名，失败返回空字符串"""
    if not patient or not hasattr(patient, 'name_enc') or not patient.name_enc:
        return ''
    try:
        return enc.decrypt(patient.name_enc)
    except Exception:
        return ''


def decrypt_patient_phone(patient) -> str:
    """解密患者手机号，失败返回空字符串"""
    if not patient or not hasattr(patient, 'phone_enc') or not patient.phone_enc:
        return ''
    try:
        return enc.decrypt(patient.phone_enc)
    except Exception:
        return ''


def get_org_name(org_code: str) -> str:
    """获取机构中文名称，未知编码返回原值"""
    if not org_code:
        return '-'
    return ORG_NAME_MAP.get(org_code, org_code)


def get_disease_name(disease_code: str) -> str:
    """获取慢病类型中文名称，未知编码返回原值"""
    if not disease_code:
        return '-'
    return DISEASE_NAME_MAP.get(disease_code.upper(), disease_code)
