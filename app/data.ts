import { withBasePath } from "./basePath";

export type BranchImage = {
  src: string;
  label: string;
  inherited?: boolean;
  videoSrc?: string;
};

export type ParameterGroup = {
  title: string;
  titleEn?: string;
  items: { label: string; labelEn?: string; value: string; valueEn?: string; note?: string; noteEn?: string }[];
};

export type VersionEntry = {
  version: string;
  year: string;
  title: string;
  status: "prototype" | "calibration" | "current" | "hypothesis";
  projection: BranchImage;
  bluray: BranchImage;
  fsd?: BranchImage;
  camera?: BranchImage;
  summary: string;
  changes: string[];
  errors: string[];
  discoveries: string[];
  refs: string[];
  parameters?: ParameterGroup[];
  additionalTrials?: {
    name: string;
    note: string;
    projection: BranchImage;
    bluray: BranchImage;
    fsd?: BranchImage;
    camera?: BranchImage;
  }[];
  pipelineComparisons?: {
    name: string;
    note: string;
    noteEn: string;
    outputs: {
      title: string;
      titleEn: string;
      branch: BranchImage;
    }[];
  }[];
};

const common = (version: string): BranchImage => ({
  src: `/versions/${version}-main.jpg`,
  label: "当时尚未拆分两条观看链；这里保留同一实验主图",
  inherited: true,
});

export const versions: VersionEntry[] = [
  {
    version: "V4",
    year: "结构原型",
    title: "让清晰度与颗粒属于同一种介质",
    status: "prototype",
    projection: common("v4"),
    bluray: common("v4"),
    summary: "第一次停止在成片上覆盖噪点，改为从虚拟乳剂密度场形成图像，并让MTF和颗粒共同决定细节。",
    changes: ["建立曝光域乳剂原型", "加入通道相关的MTF", "保留逐帧随机结构"],
    errors: ["颗粒半径和观察模糊过大", "更接近8mm/16mm，而不是35mm 5279", "颜色仍主要来自经验矩阵"],
    discoveries: ["粗颗粒必须伴随较低的高频清晰度", "颗粒不是独立贴图，而是画面形成机制的一部分"],
    refs: ["R1", "R2"],
  },
  {
    version: "V5",
    year: "5279定标",
    title: "从“胶片感”转向指定片种",
    status: "prototype",
    projection: common("v5"),
    bluray: common("v5"),
    summary: "开始以Kodak VISION 500T 5279的数据表为约束，不再把所有高速彩色负片视为同一种风格。",
    changes: ["引入5279感色与曲线目标", "建立35mm画幅尺度", "开始区分R/G/B记录"],
    errors: ["高光仍受RAW解码和显示端裁切影响", "暗部颗粒偏彩色电子噪声", "三层乳剂尚未显式建模"],
    discoveries: ["5279的蓝记录颗粒测量显著高于绿、红记录", "片种性格必须由曲线、染料和颗粒共同决定"],
    refs: ["R1"],
  },
  {
    version: "V6",
    year: "RAW高光",
    title: "先救回传感器信息，再谈胶片肩部",
    status: "prototype",
    projection: common("v6"),
    bluray: common("v6"),
    summary: "修正GH7 ProRes RAW的线性解释与高光路径，把摄像机裁切和负片肩部压缩分离。",
    changes: ["保持RAW在线性域", "加入分记录高光肩部", "限制极高曝光的长程红层散射"],
    errors: ["颗粒依旧过猛", "高光光学效应曾被做成通用红光晕", "Panasonic色彩变换还不够严格"],
    discoveries: ["负片高光不是简单soft clip", "rem-jet会显著抑制背面散射，5279不应出现夸张光晕"],
    refs: ["R1", "R2", "R3"],
  },
  {
    version: "V7",
    year: "胶片光学",
    title: "把卤化银、散射与防光晕放进同一条链",
    status: "prototype",
    projection: common("v7"),
    bluray: common("v7"),
    summary: "补入乳剂层散射、防光晕层和局部边缘响应，画面开始从均匀噪声变成密度相关的结构。",
    changes: ["曝光相关颗粒", "受控halation", "颗粒与边缘响应耦合"],
    errors: ["形态仍像被推冲的16mm", "三种速度层只是宏观分段", "黑位和观看条件尚未分离"],
    discoveries: ["暗部、亮部的颗粒差异来自不同速度群体进入显影区间", "清晰度匹配比单纯降低噪点更重要"],
    refs: ["R2", "R3"],
  },
  {
    version: "V8",
    year: "35mm细化",
    title: "从生猛16mm收回到细腻35mm",
    status: "calibration",
    projection: common("v8"),
    bluray: common("v8"),
    summary: "缩小染料云、提高有效位点数量、减弱暗部密度摆幅，让颗粒频率和5279的35mm观感接近。",
    changes: ["颗粒半径降至约0.5–1.3原生像素", "增加有效染料云数量", "减弱暗部彩色分离"],
    errors: ["平均响应仍依赖共享曲线", "扫描和放映还没有各自的物理观察器", "染料遮罩没有光谱化"],
    discoveries: ["细腻并不等于静止：更小、更密的位点仍可产生有机逐帧变化"],
    refs: ["R1", "R2"],
  },
  {
    version: "V9",
    year: "双分支起点",
    title: "5279负片曲线、光谱染料与两种观看结果",
    status: "calibration",
    projection: { src: "/versions/v9-projection.jpg", label: "早期正片解释" },
    bluray: { src: "/versions/v9-bluray.jpg", label: "5279负片扫描解释" },
    summary: "首次分别采样5279红、绿、蓝Status-M曲线，并建立扫描与印片两条观看分支。",
    changes: ["三条独立H-D曲线", "净染料密度的初步光谱模型", "扫描与正片分离"],
    errors: ["正片仍是经验性正值染料矩阵", "未完整保留橙色底和有色耦合剂的负密度瓣", "两条分支的色彩基准不统一"],
    discoveries: ["5279数据表的染料曲线是D-min已扣除的净变化，并非纯染料吸收", "遮罩耦合剂必须只计算一次"],
    refs: ["R1", "R2", "R4"],
  },
  {
    version: "V10",
    year: "2383初版",
    title: "把Kodak 2383作为第二种真实材料",
    status: "calibration",
    projection: { src: "/versions/v10-projection.jpg", label: "5279 → 2383 初版" },
    bluray: { src: "/versions/v9-bluray.jpg", label: "扫描分支沿用V9", inherited: true },
    summary: "加入2383的感光曲线、染料和印片灯，使放映不再是对负片做一条显示LUT。",
    changes: ["第二套H-D曲线", "LAD目标密度", "2383染料与正片颗粒"],
    errors: ["曾把净负密度曲线当成纯正值染料，造成严重紫红偏色", "橙色底被错误去除或重复补偿", "正片陡峭曲线放大了小型光谱误差"],
    discoveries: ["光学印片必须保留5279 D-min/橙色底在光路中", "扫描去底与印片补偿不是同一操作"],
    refs: ["R1", "R3", "R4"],
  },
  {
    version: "V11",
    year: "灰阶校准",
    title: "不只校准18%灰，而是校准整条灰阶",
    status: "calibration",
    projection: { src: "/versions/v11-projection.jpg", label: "2383氙灯放映" },
    bluray: { src: "/versions/v11-bluray.jpg", label: "Cineon / Spirit 2K扫描" },
    summary: "用LAD与多级灰阶约束中性，建立Cineon编码和Spirit式扫描基础。",
    changes: ["多点中性灰校准", "Cineon代码值95/445锚点", "两条分支统一Rec.709输出"],
    errors: ["局部颜色仍由粗糙矩阵修正", "扫描器光谱被近似为Status-M", "蓝光完成阶段黑位尚未单独设计"],
    discoveries: ["中灰中性并不能保证高光和暗部中性", "黑位是观看链决策，不应倒推修改负片D-min"],
    refs: ["R5", "R8"],
  },
  {
    version: "V12",
    year: "有色遮罩",
    title: "保留有色耦合剂的净负密度",
    status: "calibration",
    projection: { src: "/versions/v12-projection.jpg", label: "修正遮罩后的放映" },
    bluray: { src: "/versions/v12-bluray.jpg", label: "修正遮罩后的扫描" },
    summary: "将5279数据表的21点光谱曲线作为带符号的净密度变化，正确解释有色遮罩。",
    changes: ["21波长光谱LUT", "保留小型负密度瓣", "DIR局部邻接初版"],
    errors: ["扫描端仍使用窄带观察器", "DIR在总密度形成后才计算", "色彩分离缺少亚层依赖"],
    discoveries: ["负值不是数据错误，而是遮罩耦合剂被消耗的方向", "平均校正平坦仍会留下片种特有的光谱残差"],
    refs: ["R1", "R2", "R3", "R6"],
  },
  {
    version: "V13",
    year: "投影光源",
    title: "从黑体白光改为电影氙灯光谱",
    status: "calibration",
    projection: { src: "/versions/v13-projection.jpg", label: "修正后的2383氙灯放映" },
    bluray: { src: "/versions/v13-bluray.jpg", label: "Spirit 2K扫描" },
    summary: "加入氙灯的非平滑光谱结构、CIE观察器和投影散射。早期放映版的紫红错误也被明确记录并修正。",
    changes: ["氙灯SPD", "CIE XYZ观察", "Callier/投影散射的保守近似"],
    errors: ["第一版放映严重紫红，根因是打印光谱与染料解释叠加错误", "显示器上观看物理放映结果时，对比和色浓度过强"],
    discoveries: ["“物理投影”与“在显示器上呈现投影质感”需要两个不同目标", "小色相误差会被2383陡峭曲线放大"],
    refs: ["R2", "R4", "R7"],
  },
  {
    version: "V14",
    year: "三速度层",
    title: "有限快／中／慢感光位点",
    status: "calibration",
    projection: { src: "/versions/v14-projection.jpg", label: "多层颗粒放映" },
    bluray: { src: "/versions/v14-bluray.jpg", label: "多层颗粒扫描" },
    summary: "每个颜色记录拥有快、中、慢三组有限位点，以二项统计形成曝光相关颗粒，并严格回标5279的48µm RMS曲线。",
    changes: ["9组有限位点", "p(1−p)方差", "48µm测量孔径校准"],
    errors: ["R/G/B共用一套代表性颗粒尺寸", "每组内部仍是单一圆形尺寸", "颗粒颜色相关性不够有机"],
    discoveries: ["位点接近全显影时方差会再次下降", "‘阴影粗、亮部细’是群体转换，不是简单亮度遮罩"],
    refs: ["R1", "R2", "R7"],
  },
  {
    version: "V15",
    year: "完整印片光路",
    title: "橙色底、印片灯、2383与色域映射",
    status: "calibration",
    projection: { src: "/versions/v15-projection.jpg", label: "完整光谱印片链" },
    bluray: { src: "/versions/v15-bluray.jpg", label: "扫描链校准" },
    summary: "在全波长光路中保留橙色底，用印片灯补偿并通过2383形成正片；加入RGB分离补偿。",
    changes: ["D-min全光谱传输", "印片灯中性补偿", "H-61/TAF式颜色分离校准"],
    errors: ["投影颜色仍偏深、偏蓝", "暗红和绿色曾发生大角度色相旋转", "扫描黑位与颗粒积分顺序仍有问题"],
    discoveries: ["投影浓郁感一部分是2383斜率，另一部分可能是错误观看适配", "色域压缩必须尽量保持恒定色相"],
    refs: ["R3", "R4", "R5"],
  },
  {
    version: "V16",
    year: "观看链校准",
    title: "放映黑、扫描黑与色相稳定",
    status: "calibration",
    projection: { src: "/versions/v16-projection.jpg", label: "典型16 ft-L放映" },
    bluray: { src: "/versions/v16-bluray.jpg", label: "2K DI / 蓝光完成" },
    summary: "分离无杂散光投影、典型影院投影和蓝光完成；用OKLab恒色相压缩修正暗部色偏。",
    changes: ["典型1%投影flare", "OKLab恒色相压缩", "蓝光下段gamma与真实黑锚点"],
    errors: ["蓝光颗粒会在显示黑边界形成单边偏置", "投影在显示器上仍显得过重", "扫描高频彩色颗粒多于参考影片"],
    discoveries: ["投影黑位和蓝光黑位来自不同物理/显示链", "《霹雳娇娃2》只能约束完成态，不能当作未调色5279测量"],
    refs: ["R8", "R9", "R10"],
  },
  {
    version: "V17",
    year: "扫描修正",
    title: "在透射光域完成Spirit 2K积分",
    status: "calibration",
    projection: { src: "/versions/v16-projection.jpg", label: "放映分支沿用V16", inherited: true },
    bluray: { src: "/versions/v17-bluray.jpg", label: "V17透射域扫描" },
    summary: "扫描器先对穿过负片的光做2K面积积分，再转回密度和Cineon，解决黑场被颗粒抬起的问题。",
    changes: ["透射域2K孔径", "显示边界之后才形成", "蓝光高频色度颗粒受控积分"],
    errors: ["物理放映与显示器观看仍未适配", "扫描观察器仍近似Status-M", "颗粒形态还太规则"],
    discoveries: ["扫描器看到的是透射光，不是已经裁到黑的正片RGB", "正确的运算顺序本身就能修复浮黑"],
    refs: ["R8", "R10"],
  },
  {
    version: "V18",
    year: "显示适配",
    title: "区分物理2383投影与显示器上的放映质感",
    status: "calibration",
    projection: { src: "/versions/v18-projection.jpg", label: "2383显示器观看适配" },
    bluray: { src: "/versions/v17-bluray.jpg", label: "蓝光分支沿用V17", inherited: true },
    summary: "保留物理投影分支，同时建立适合Rec.709显示器判断的投影外观；分离GH7传感器噪声和虚拟乳剂颗粒。",
    changes: ["投影monitor分支", "中性灰多锚点适配", "场景线性传感器噪声分离"],
    errors: ["早期适配仍有轻微蓝偏和强色区域偏移", "粗晶群体规则性仍可见"],
    discoveries: ["感知到的蓝偏主要是非线性对比/色度比例，而不一定是白平衡", "相机噪声不能被误当成胶片颗粒保留"],
    refs: ["R7", "R8"],
  },
  {
    version: "V19",
    year: "有机颗粒",
    title: "多分散染料云与逐帧沸腾",
    status: "calibration",
    projection: { src: "/versions/v19-projection.jpg", label: "有机颗粒放映" },
    bluray: { src: "/versions/v19-bluray.jpg", label: "有机颗粒蓝光" },
    summary: "每个速度群体拆为三种尺寸类别，加入亚像素相位和稀疏大云，使颗粒运动减少数字彩噪感。",
    changes: ["多分散尺寸", "亚像素相位", "小颗粒占主导、稀疏大云提供生命力"],
    errors: ["亚层的颜色贡献仍静态", "DIR仍在亚层合并之后", "所有颜色记录仍共享代表性ECD"],
    discoveries: ["有机感来自统计形态的不规则与连续尺寸，而不是增大噪点", "逐帧新采样必须保持密度均值不漂移"],
    refs: ["R1", "R2", "R7"],
  },
  {
    version: "V20",
    year: "上一版",
    title: "曝光相关的亚层染料贡献",
    status: "calibration",
    projection: { src: "/versions/v20-projection.jpg", label: "V20 · 2383放映" },
    bluray: { src: "/versions/v20-bluray.jpg", label: "V20 · 2K DI / 蓝光" },
    summary: "快、中、慢层根据边际激活量改变色记录贡献；薄负片的颜色分离更宽，高曝光慢层更接近纯记录。",
    changes: ["边际激活混色", "颗粒与色彩形成首次耦合", "扫描肩部校正更自然地释放"],
    errors: ["DIR仍是总密度后的二维近似", "扫描器和Status-M仍被混为同一个观察器", "亚层尺寸没有按颜色记录独立"],
    discoveries: ["柯达同期专利显示胶片设计会预补偿Telecine红通道", "彩色负片最终承载影像的是染料云，显影银影会被移除", "V21必须重排算法顺序，而不是继续调矩阵"],
    refs: ["R2", "R3", "R6", "R11", "R12"],
  },
  {
    version: "V21",
    year: "上一版",
    title: "让显影、颗粒与观察器真正分开工作",
    status: "calibration",
    projection: { src: "/versions/v21-projection.jpg", label: "V21 · 2383氙灯放映显示适配" },
    bluray: { src: "/versions/v21-bluray.jpg", label: "V21 · Period 2K / Cineon蓝光" },
    summary: "DIR改在九个快／中／慢群体显影时发生；三条颜色记录拥有独立颗粒形态；Status-M、时期Telecine和2383印片成为三个不同的光谱观察器。与此同时修正了V20放映版几乎继承扫描版色度、只留下更深黑位的错误。",
    changes: ["九群体显影域DIR反应—扩散", "青／品红／黄记录独立快中慢形态", "Status-M、Period 2K、2383三观察器分离", "重建2383显示器观看适配，不再复制扫描色相与饱和度"],
    errors: ["V20的投影显示适配从扫描分支继承约92%色相和94%饱和度，使两张截图除了黑位外过度接近", "5279真实亚层配方与时期Telecine精确光谱仍未公开，当前参数是受数据表和同期专利约束的模型", "显示器上的放映版仍是对16 ft-L影院观看的适配，不等同于银幕实测光谱"],
    discoveries: ["中性H-D可以在DIR重排后保持到约2.4×10⁻⁷ D，同时让局部与层间反应发生", "48µm孔径下三记录RMS误差保持在约0–1.5%", "放映与扫描应共享中性明度目标，却不能共享色度；V21代表帧的中位色相差约4.8°"],
    refs: ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R11", "R12"],
  },
  {
    version: "V22",
    year: "上一版",
    title: "分析染料、层间耦合与相对白点放映预览",
    status: "calibration",
    projection: { src: "/versions/v22-projection.jpg", label: "V22 · 5279 → 2383氙灯放映" },
    bluray: { src: "/versions/v22-bluray.jpg", label: "V22 · Period 2K / Cineon蓝光" },
    summary: "修正V21把2383 Status-A积分密度再次当作独立CMY染料量的结构错误：先非线性反解分析染料量，再经LAD锚定的层间曝光耦合进入正片曲线。物理胶片与显示器预览被明确拆分，D60目标只提供去除自身中性白点后的相对色度校准。",
    changes: ["非线性Status-A积分密度→分析染料量反演", "LAD锚定的印片层间曝光矩阵", "去除D60中性响应的显示器相对色度校准", "放映与扫描共享同一帧5279乳剂随机实现"],
    errors: ["V21把积分测量值再次乘以染料光谱，重复计算了不希望吸收", "D60是公开厂商的显示目标，不是Kodak工厂化学参数", "5279实拍色卡、肤色靶和影院分光测量仍未获得；当前母版只有6帧"],
    discoveries: ["公开胶片化学只约束胶片与氙灯，影院外观转到Rec.709还需要独立观看适配", "厂商D60变换的绝对白点必须先减去，否则会把整张画面染紫红", "13项三次多项式无法压缩该非线性修正，25³相对色度格点才通过保持测试", "六色中位色相误差从V21的7.94°降至1.46°；实拍帧进入D55–D65色相包络的像素从20.2%升至45.9%"],
    refs: ["R1", "R4", "R5", "R16", "R17", "R18", "R19", "R20"],
    parameters: [
      { title: "输入与母版", items: [
        { label: "源素材", value: "GH7 Open Gate ProRes RAW HQ" },
        { label: "RAW解码", value: "Apple extended-linear BT.2020 · float32" },
        { label: "相机色彩", value: "Panasonic官方RAW → V-Gamut" },
        { label: "虚拟曝光", value: "+0.45 stop" },
        { label: "画幅", value: "5760 × 4320 · 4:3" },
        { label: "帧率", value: "24000/1001 · 23.976 fps" },
        { label: "测试段", value: "Frame 9–14 · 6帧" },
        { label: "母版", value: "ProRes 4444 · yuv444p12le" },
        { label: "显示编码", value: "Rec.709 · 1-1-1" },
      ] },
      { title: "5279乳剂", items: [
        { label: "片种", value: "KODAK VISION 500T 5279" },
        { label: "假定成像宽", value: "24.9 mm" },
        { label: "亚层结构", value: "R/G/B × 快/中/慢 × 3粒径" },
        { label: "速度偏移", value: "0.00 / 0.50 / 1.30 logE" },
        { label: "容量比例 快/中/慢", value: "126 / 149 / 161" },
        { label: "快层中心 R/G/B", value: "−2.034 / −2.018 / −2.112 logE" },
        { label: "转折宽度 R/G/B", value: "0.550 / 0.572 / 0.525" },
        { label: "ECD 青记录", value: "1.28 / 0.83 / 0.58 µm" },
        { label: "ECD 品红记录", value: "1.36 / 0.79 / 0.52 µm" },
        { label: "ECD 黄记录", value: "1.14 / 0.88 / 0.68 µm" },
        { label: "颗粒校准孔径", value: "48 µm diffuse RMS" },
        { label: "颗粒相关尺度", value: "0.88" },
        { label: "粒径占比", value: "0.30 / 0.53 / 0.17" },
        { label: "粒径半径倍率", value: "0.70 / 1.00 / 1.42" },
        { label: "光学倍率", value: "0.82 / 1.00 / 1.20" },
        { label: "亚像素相位半径", value: "0.38 px @ 5760" },
        { label: "光学σ 青记录", value: "0.59 / 0.43 / 0.34 px" },
        { label: "光学σ 品红记录", value: "0.63 / 0.41 / 0.31 px" },
        { label: "光学σ 黄记录", value: "0.54 / 0.45 / 0.37 px" },
        { label: "有效位点 青记录", value: "17 / 60 / 79 px⁻¹" },
        { label: "有效位点 品红记录", value: "16 / 64 / 88 px⁻¹" },
        { label: "有效位点 黄记录", value: "22 / 55 / 70 px⁻¹" },
        { label: "负片MTF σ R/G/B", value: "0.85 / 0.67 / 0.60 px" },
        { label: "感色重叠 Row R", value: "0.94 / 0.05 / 0.01" },
        { label: "感色重叠 Row G", value: "0.04 / 0.92 / 0.04" },
        { label: "感色重叠 Row B", value: "0.01 / 0.08 / 0.91" },
      ] },
      { title: "DIR显影耦合", items: [
        { label: "发生阶段", value: "九亚层合并前的显影域" },
        { label: "扩散σ 快/中/慢", value: "4.8 / 3.1 / 1.9 px @ 5760" },
        { label: "层间强度", value: "0.085" },
        { label: "层内强度 R/G/B", value: "0.028 / 0.042 / 0.058" },
        { label: "随机耦合", value: "0.42" },
        { label: "释放增益 快/中/慢", value: "0.90 / 1.00 / 0.82" },
        { label: "接收增益 快/中/慢", value: "0.72 / 1.00 / 0.84" },
        { label: "传输矩阵 Row 1", value: "0.34 / 0.22 / 0.10" },
        { label: "传输矩阵 Row 2", value: "0.22 / 0.30 / 0.18" },
        { label: "传输矩阵 Row 3", value: "0.10 / 0.18 / 0.24" },
        { label: "中性约束", value: "均匀H-D严格不漂移" },
      ] },
      { title: "2383放映链", items: [
        { label: "正片", value: "KODAK VISION 2383" },
        { label: "Status-A D-min R/G/B", value: "0.04356 / 0.04749 / 0.10272 D" },
        { label: "LAD目标", value: "1.00 D" },
        { label: "D-max", value: "4.10 D" },
        { label: "印片光", value: "3200 K" },
        { label: "放映光", value: "Kodak参考氙灯SPD" },
        { label: "Callier修正", value: "1.0–1.4% density" },
        { label: "典型影院flare", value: "1.0%" },
        { label: "正片MTF σ R/G/B", value: "0.34 / 0.27 / 0.52 px" },
        { label: "层间矩阵 Row 1", value: "1.4105 / −0.9566 / 0.9152" },
        { label: "层间矩阵 Row 2", value: "0.4127 / 0.6943 / −0.2324" },
        { label: "层间矩阵 Row 3", value: "−0.5640 / 0.6093 / 0.8425", note: "识别值，不宣称是Kodak工厂矩阵" },
      ] },
      { title: "显示器放映预览", items: [
        { label: "物理亮度权重", value: "0.50" },
        { label: "最大物理色相权重", value: "1.00" },
        { label: "最大物理饱和权重", value: "0.60" },
        { label: "色度校准", value: "D60相对Oklab a/b · L不变" },
        { label: "校准格点", value: "25³ × 3" },
        { label: "中性保护", value: "Cineon chroma 0.008 → 0.040" },
        { label: "插值余量", value: "0.99" },
        { label: "扫描亮度锚点", value: "0 / .00087 / .00863 / .03523 / .09330 / .18 / .27646 / .38707 / .51532 / .66216 / 1" },
        { label: "目标亮度锚点", value: "0 / .00320 / .01010 / .02374 / .06445 / .17997 / .36756 / .54039 / .67413 / .78203 / .97460" },
        { label: "色域映射", value: "Oklab恒色相压缩" },
      ] },
      { title: "Period 2K / 蓝光", items: [
        { label: "扫描观察器", value: "Spirit式宽带RGB · 620/540/470 nm" },
        { label: "扫描孔径", value: "2048 RGB line-array" },
        { label: "Cineon", value: "10-bit · black 95 · 0.002 D/CV" },
        { label: "中性灰码值", value: "445" },
        { label: "主色校正强度", value: "0.82" },
        { label: "肩部释放", value: "0.04" },
        { label: "蓝光下段gamma", value: "1.20" },
        { label: "色度颗粒σ", value: "0.55 @ 2K" },
        { label: "高频色度保留", value: "0.55" },
        { label: "硬件Grain Manager", value: "Off" },
      ] },
    ],
  },
  {
    version: "V23",
    year: "当前版本",
    title: "连续染料云群体与跨场景颜色保持",
    status: "current",
    projection: { src: "/versions/v23-t020-projection.jpg", label: "T020 · 5279 → 2383氙灯放映" },
    bluray: { src: "/versions/v23-t020-bluray.jpg", label: "T020 · Period 2K / Cineon蓝光" },
    summary: "在树皮、蘑菇、亮叶与天空，以及雨天青绿场景上复测V22颜色；拒绝了没有实际收益的D55/D60/D65三白点候选。颗粒由三种离散尺寸改成五点连续分布近似，并以黄金角改变亚像素相位，使沸腾更细、更不规则，同时继续回标5279公开的48µm RMS。",
    changes: ["两段新GH7 ProRes RAW各制作1秒双母版，用短片先验证方向", "三尺寸染料云改为五点连续分布近似", "黄金角亚像素相位减少规则重复", "颗粒相关尺度0.88降至0.86", "193³完整放映映射加速并逐像素验证", "记录真实并行制作时间"],
    errors: ["D55/D60/D65三白点相对色度候选与V22 D60结果数值上几乎相同，因此被拒绝", "公开数据仍未给出5279真实染料云尺寸分布；五点分布是受颗粒、MTF与同期结构约束的数值近似", "5279快/中/慢层的真实成色剂量和分层染料光谱未公开；当前曝光相关染料贡献仍是受限模型", "193³加速格点在极少数非线性边界点仍有局部误差；真实帧99%像素Oklab ΔE小于约0.36"],
    discoveries: ["颜色候选必须在新场景上产生可测收益，否则保持已验证模型比继续调色更准确", "颗粒的有机性可由尺寸连续性和相位非周期性提高，不需要增加RMS幅度", "同期Kodak结构会限制最高速层的成色剂量；暗部色噪与分层染料形成相互耦合", "完整物理颜色链可被高密度格点安全缓存；真实帧逐像素放映变换约加速14倍", "T020和T032分别考验高光/暗树皮与青绿/低对比场景，适合作为以后版本的固定泛化测试"],
    refs: ["R1", "R2", "R4", "R7", "R21", "R22", "R23", "R24"],
    additionalTrials: [{
      name: "NJARAW_S001_S001_T032",
      note: "雨天青绿、暗柱与湿地低对比场景；用于检查绿色色相、阴影颗粒和扫描黑位。",
      projection: { src: "/versions/v23-t032-projection.jpg", label: "T032 · 5279 → 2383氙灯放映" },
      bluray: { src: "/versions/v23-t032-bluray.jpg", label: "T032 · Period 2K / Cineon蓝光" },
    }],
    parameters: [
      { title: "输入与母版", items: [
        { label: "源素材 A", value: "NJARAW_S001_S001_T020" },
        { label: "源素材 B", value: "NJARAW_S001_S001_T032" },
        { label: "相机 / 记录", value: "Panasonic GH7 · Atomos Ninja · ProRes RAW HQ" },
        { label: "拍摄参数", value: "ISO 500 · 5500 K · 180°" },
        { label: "RAW解码", value: "Apple extended-linear BT.2020 · float32" },
        { label: "相机色彩", value: "Panasonic官方RAW → V-Gamut" },
        { label: "虚拟曝光", value: "+0.45 stop" },
        { label: "画幅 / 帧率", value: "5760 × 4320 · 24000/1001" },
        { label: "每段长度", value: "24帧 · 1.001秒" },
        { label: "母版", value: "ProRes 4444 · yuv444p12le" },
        { label: "显示编码", value: "Rec.709 · 1-1-1" },
      ] },
      { title: "5279乳剂与颗粒", items: [
        { label: "片种 / 成像宽", value: "VISION 500T 5279 · 24.9 mm" },
        { label: "亚层结构", value: "R/G/B × 快/中/慢 × 5粒径" },
        { label: "速度偏移", value: "0.00 / 0.50 / 1.30 logE" },
        { label: "容量比例 快/中/慢", value: "126 / 149 / 161" },
        { label: "快层中心 R/G/B", value: "−2.034 / −2.018 / −2.112 logE" },
        { label: "转折宽度 R/G/B", value: "0.550 / 0.572 / 0.525" },
        { label: "ECD 青记录", value: "1.28 / 0.83 / 0.58 µm" },
        { label: "ECD 品红记录", value: "1.36 / 0.79 / 0.52 µm" },
        { label: "ECD 黄记录", value: "1.14 / 0.88 / 0.68 µm" },
        { label: "颗粒校准", value: "Kodak 48 µm diffuse RMS" },
        { label: "颗粒相关尺度", value: "0.86" },
        { label: "五级占比", value: "0.10 / 0.24 / 0.34 / 0.22 / 0.10" },
        { label: "半径倍率", value: "0.62 / 0.78 / 0.98 / 1.22 / 1.55" },
        { label: "光学倍率", value: "0.78 / 0.88 / 1.00 / 1.12 / 1.25" },
        { label: "相位步进", value: "2.399963 rad · 黄金角" },
        { label: "亚像素相位半径", value: "0.38 px @ 5760" },
        { label: "光学σ 青记录", value: "0.59 / 0.43 / 0.34 px" },
        { label: "光学σ 品红记录", value: "0.63 / 0.41 / 0.31 px" },
        { label: "光学σ 黄记录", value: "0.54 / 0.45 / 0.37 px" },
        { label: "有效位点 青记录", value: "17 / 60 / 79 px⁻¹" },
        { label: "有效位点 品红记录", value: "16 / 64 / 88 px⁻¹" },
        { label: "有效位点 黄记录", value: "22 / 55 / 70 px⁻¹" },
        { label: "随机种子", value: "逐帧、逐记录、逐速度群独立" },
        { label: "负片MTF σ R/G/B", value: "0.85 / 0.67 / 0.60 px" },
        { label: "感色重叠 Row R", value: "0.94 / 0.05 / 0.01" },
        { label: "感色重叠 Row G", value: "0.04 / 0.92 / 0.04" },
        { label: "感色重叠 Row B", value: "0.01 / 0.08 / 0.91" },
        { label: "传感器噪声", value: "photochemical separation" },
      ] },
      { title: "DIR显影耦合", items: [
        { label: "DIR阶段", value: "九亚层合并前的显影域" },
        { label: "DIR扩散σ", value: "4.8 / 3.1 / 1.9 px" },
        { label: "层间强度", value: "0.085" },
        { label: "层内强度 R/G/B", value: "0.028 / 0.042 / 0.058" },
        { label: "随机耦合", value: "0.42" },
        { label: "释放增益 快/中/慢", value: "0.90 / 1.00 / 0.82" },
        { label: "接收增益 快/中/慢", value: "0.72 / 1.00 / 0.84" },
        { label: "传输矩阵 Row 1", value: "0.34 / 0.22 / 0.10" },
        { label: "传输矩阵 Row 2", value: "0.22 / 0.30 / 0.18" },
        { label: "传输矩阵 Row 3", value: "0.10 / 0.18 / 0.24" },
        { label: "中性约束", value: "均匀H-D严格不漂移" },
      ] },
      { title: "染料与2383放映", items: [
        { label: "5279染料", value: "D-min已扣除的带符号净光谱密度" },
        { label: "2383分析染料", value: "非线性Status-A积分反演" },
        { label: "Status-A D-min R/G/B", value: "0.04356 / 0.04749 / 0.10272 D" },
        { label: "LAD目标 / D-max", value: "1.00 D / 4.10 D" },
        { label: "印片 / 放映光", value: "3200 K / Kodak氙灯SPD" },
        { label: "层间矩阵 Row 1", value: "1.4105 / −0.9566 / 0.9152" },
        { label: "层间矩阵 Row 2", value: "0.4127 / 0.6943 / −0.2324" },
        { label: "层间矩阵 Row 3", value: "−0.5640 / 0.6093 / 0.8425", note: "识别值，不宣称是Kodak工厂矩阵" },
        { label: "物理亮度权重", value: "0.50" },
        { label: "最大物理色相权重", value: "1.00" },
        { label: "最大物理饱和权重", value: "0.60" },
        { label: "显示色度校准", value: "D60相对Oklab a/b · L不变" },
        { label: "相对色度格点", value: "25³ × 3" },
        { label: "中性保护", value: "Cineon chroma 0.008 → 0.040" },
        { label: "颜色决定", value: "沿用V22", note: "三白点候选没有产生可测泛化收益" },
        { label: "扫描亮度锚点", value: "0 / .00087 / .00863 / .03523 / .09330 / .18 / .27646 / .38707 / .51532 / .66216 / 1" },
        { label: "目标亮度锚点", value: "0 / .00320 / .01010 / .02374 / .06445 / .17997 / .36756 / .54039 / .67413 / .78203 / .97460" },
        { label: "色域映射", value: "Oklab恒色相压缩" },
      ] },
      { title: "扫描与放映输出", items: [
        { label: "扫描观察器", value: "Spirit式宽带RGB · 620/540/470 nm" },
        { label: "扫描孔径", value: "2048 RGB line-array" },
        { label: "Cineon", value: "10-bit · black 95 · 0.002 D/CV · gray 445" },
        { label: "主色校正强度", value: "0.82" },
        { label: "肩部释放", value: "0.04" },
        { label: "蓝光下段gamma", value: "1.20" },
        { label: "色度颗粒σ / 高频", value: "0.55 @ 2K / 0.55" },
        { label: "正片MTF σ R/G/B", value: "0.34 / 0.27 / 0.52 px" },
        { label: "典型影院flare", value: "1.0%" },
        { label: "Callier修正", value: "1.0–1.4% density" },
        { label: "硬件Grain Manager", value: "Off" },
        { label: "共享乳剂随机实现", value: "是" },
      ] },
      { title: "数值验证与效率", items: [
        { label: "放映缓存格点", value: "193³ · exact analytical samples" },
        { label: "真实帧平均ΔE", value: "0.047–0.064 Oklab" },
        { label: "真实帧p99 ΔE", value: "0.307–0.359 Oklab" },
        { label: "逐像素放映加速", value: "约14×" },
        { label: "单帧双母版探测", value: "166.23秒（含封装与哈希）" },
        { label: "T020计算到第24帧", value: "3472.0秒 · 57分52秒" },
        { label: "T032计算到第24帧", value: "3551.5秒 · 59分11.5秒" },
        { label: "两段并行总等待", value: "约3551.5秒 · 59分11.5秒" },
        { label: "停止后整理", value: "T020 6.25秒 / T032 6.02秒", note: "无损取前24帧、补元数据、截图与哈希" },
        { label: "阶段计时", value: "未伪造", note: "原72帧任务在用户改为1秒时中止；内存中的阶段数组未落盘，只保留真实总墙钟" },
      ] },
    ],
  },
];

// V24 deliberately inherits the complete V23 parameter record and replaces
// only the measured texture terms. This keeps the side panel exhaustive while
// making it obvious that colour, tone, MTF and sensitometry were held fixed.
const v23 = versions[versions.length - 1];
v23.year = "上一版";
v23.status = "calibration";

const v24Overrides: Record<string, string> = {
  "颗粒相关尺度": "0.76",
  "五级占比": "0.16 / 0.30 / 0.32 / 0.17 / 0.05",
  "半径倍率": "0.50 / 0.68 / 0.86 / 1.08 / 1.34",
  "光学倍率": "0.68 / 0.80 / 0.92 / 1.05 / 1.18",
  "色度颗粒σ / 高频": "0.72 @ 2K / 0.30 · opponent 0.64",
  "真实帧平均ΔE": "与V23完全相同（平均颜色链未改）",
  "真实帧p99 ΔE": "与V23完全相同（平均颜色链未改）",
};

const v23TimingLabels = new Set([
  "单帧双母版探测", "T020计算到第24帧", "T032计算到第24帧",
  "两段并行总等待", "停止后整理", "阶段计时",
]);

const v24Parameters = (v23.parameters ?? []).map((group) => ({
  ...group,
  items: [
    ...group.items
      .filter((item) => group.title !== "数值验证与效率" || !v23TimingLabels.has(item.label))
      .map((item) => v24Overrides[item.label] ? { ...item, value: v24Overrides[item.label] } : item),
    ...(group.title === "扫描与放映输出" ? [
      { label: "放映色度颗粒积分", value: "σ 0.62 @ 2K · 高频0.36 · opponent 0.66" },
      { label: "颗粒平均色约束", value: "只作用于signed delta；均值分支不变" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "V24 48µm RMS误差", value: "约0.6–1.4%" },
      { label: "T020综合色/明度颗粒", value: "放映1.58 → 0.93 · 扫描1.72 → 0.92" },
      { label: "T032综合色/明度颗粒", value: "放映2.07 → 1.15 · 扫描2.11 → 1.08" },
      { label: "V24平均颜色最大变化", value: "0.000000（数值精确不变）" },
      { label: "T020真实总墙钟", value: "3450.98秒 · 57分31秒" },
      { label: "T032真实总墙钟", value: "3511.76秒 · 58分32秒" },
      { label: "两段并行总等待", value: "3511.76秒 · 58分32秒" },
      { label: "乳剂形成 / 帧", value: "T020 77.53秒 · T032 77.60秒" },
      { label: "平均负片 / 帧", value: "31.58秒 · 32.67秒" },
      { label: "投影 / 扫描 / 帧", value: "约17.3秒 / 15.9–16.9秒" },
      { label: "解码 / 双路编码 / 帧", value: "约0.85–1.01秒 / 0.31–0.44秒" },
      { label: "性能瓶颈", value: "45组全画幅有限位点二项采样", note: "现场调用栈主要落在NumPy binomial；编码、解码与磁盘不是瓶颈" },
      { label: "现场硬件利用", value: "16核 / 48GB；采样时CPU约80%空闲", note: "参考实现未有效并行化最重随机步骤，不代表硬件弱" },
      { label: "网页观察空间", value: "sRGB IEC 61966-2-1 · D65", note: "静态图与短视频使用同一显示变换；5.7K 12-bit Rec.709母版保持不变" },
      { label: "网页帧对齐", value: "第13帧静态图 = 短视频首帧", note: "24帧循环重排为13–24、1–12，悬停切换不再跳画面" },
      { label: "网页Live预览", value: "1280 × 960 · H.264 · 24fps · 1.001秒", note: "sRGB网页代理；逐片验证视频首帧与大图的综合色及中间调误差" },
    ] : []),
  ],
}));

versions.push({
  version: "V24",
  year: "当前版本",
  title: "35mm颗粒频谱与综合色分离",
  status: "current",
  projection: { src: "/versions/v24-t020-projection.jpg", label: "T020 · 5279 → 2383氙灯放映" },
  bluray: { src: "/versions/v24-t020-bluray.jpg", label: "T020 · Period 2K / Cineon蓝光" },
  summary: "回应V23更像早期CCD或16mm的观感：V24不重调颜色，而是把公开的48µm RMS与完整空间频谱区分开。五级染料云向较小尺度重新分配，并在放映与扫描的观察阶段只积分综合色颗粒，保留明度颗粒的逐帧有机沸腾。平均色彩、黑白灰、负片MTF、2383与Cineon链均保持V23。",
  changes: ["染料云尺寸分布向35mm细颗粒端移动", "减少大云占比和总体相关尺度", "放映与扫描分别加入综合色颗粒积分", "完整保留明度颗粒与逐帧随机实现", "平均颜色与色调分支保持数值不变", "两段新素材继续各做1秒5.7K 12-bit双母版", "V24四个画面改为1秒Live网页预览，保留静帧放大与左右导航"],
  errors: ["V23虽然改善了离散颗粒形态，但综合色颗粒仍过强，容易被识别为RGB彩噪或早期CCD", "48µm RMS只约束特定孔径下的幅度，不能单独决定颗粒的粗细、低频成团和最终观看尺度", "公开文件没有5279完整Wiener/NPS曲线；V24的尺寸分布仍是受边界约束的模型选择，不是秘方复原", "黑白灰和创作调色没有在V24内重做；这样可以把颗粒判断与调色判断分离"],
  discoveries: ["35mm与16mm的显著差别不只是RMS大小，还包括放大倍率、低频功率与输出链MTF", "将颗粒做小后重新回标48µm RMS不会让它自动变安静，观察器对综合色与明度纹理的积分同样重要", "综合色颗粒可以在signed grain delta中独立处理，因此减少CCD感而不改变平均色相或饱和度", "T020与T032的综合色/明度颗粒比都显著下降，而平均输出的最大绝对差为零"],
  refs: ["R1", "R4", "R7", "R8", "R21", "R22", "R23", "R25"],
  additionalTrials: [{
    name: "NJARAW_S001_S001_T032",
    note: "雨天青绿和低反差细节用于验证综合色颗粒不会重新变成青绿色CCD噪声。",
    projection: { src: "/versions/v24-t032-projection.jpg", label: "T032 · 5279 → 2383氙灯放映" },
    bluray: { src: "/versions/v24-t032-bluray.jpg", label: "T032 · Period 2K / Cineon蓝光" },
  }],
  parameters: v24Parameters,
});

const v24 = versions[versions.length - 1];
v24.year = "上一版";
v24.status = "calibration";

const v25Overrides: Record<string, string> = {
  "显示编码": "Rec.709 OETF · 完整1-1-1 · 两个监看分支一致",
  "随机种子": "逐帧/记录/速度/粒径/固定条带；线程数不改变结果",
  "颜色决定": "沿用V22已验证分析染料链；不采纳未识别hourly候选",
  "网页观察空间": "Rec.709反OETF后统一转sRGB D65",
};

const v25Parameters = (v24.parameters ?? []).map((group) => ({
  ...group,
  items: [
    ...group.items
      .filter((item) => group.title !== "数值验证与效率" || ![
        "T020真实总墙钟", "T032真实总墙钟", "两段并行总等待", "乳剂形成 / 帧",
        "平均负片 / 帧", "投影 / 扫描 / 帧", "解码 / 双路编码 / 帧", "网页观察空间",
        "网页帧对齐", "网页Live预览", "性能瓶颈", "现场硬件利用",
      ].includes(item.label))
      .map((item) => v25Overrides[item.label] ? { ...item, value: v25Overrides[item.label] } : item),
    ...(group.title === "扫描与放映输出" ? [
      { label: "放映监看母版", value: "Rec.709-D65 OETF · 1-1-1", note: "内部保留2383、氙灯、48 nit与gamma 2.6影院观察，再适配到Rec.709监视器" },
      { label: "蓝光母版", value: "Rec.709-D65 OETF · 1-1-1", note: "BT.1886是参考显示EOTF，不再把其反函数写进源文件" },
      { label: "影院观看条件", value: "48 cd/m² · gamma 2.6（投影观察模型内部）" },
      { label: "蓝光观看条件", value: "BT.1886 SDR参考显示" },
      { label: "母版范围", value: "full-range RGB计算 → 12-bit 4:4:4 ProRes" },
      { label: "网页代理", value: "sRGB IEC 61966-2-1 · D65" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "V25修正一帧双母版", value: "79.77秒（含封装与哈希）" },
      { label: "V24等效一帧", value: "约143秒核心计算" },
      { label: "银盐采样 1→8线程", value: "70.09 → 35.22秒 · 1.99×" },
      { label: "线程一致性", value: "5760×4320逐像素相同 · max Δ 0" },
      { label: "复用平均负片", value: "删除每帧一次完整重复显影计算" },
      { label: "颗粒质量捷径", value: "无", note: "未减分辨率、未减45组采样、未缩短帧数、未改RMS/MTF/粒径" },
      { label: "错误版T020蓝光YAVG", value: "1354.70" },
      { label: "修正版T020蓝光YAVG", value: "1060.24", note: "V24基线1060.04；差异0.02%" },
      { label: "错误→修正YLOW", value: "557 → 304", note: "V24基线304" },
      { label: "正式T020计时", value: "1649.71秒 · 27分29.71秒" },
      { label: "正式T032计时", value: "1642.29秒 · 27分22.29秒" },
      { label: "两段并行总等待", value: "1649.71秒 · 27分29.71秒" },
      { label: "相对V24总等待", value: "58分32秒 → 27分30秒 · 缩短53.0%" },
      { label: "正式平均负片 / 帧", value: "T020 32.64秒 · T032 32.43秒" },
      { label: "正式乳剂形成 / 帧", value: "16.05秒 · 17.33秒", note: "八个固定条带worker；含完整二项抽样、DIR与RMS回标" },
      { label: "正式双观察器 / 帧", value: "18.71秒 · 16.82秒", note: "2383放映监看与Rec.709蓝光并行" },
      { label: "解码 / 双路编码 / 帧", value: "0.68–1.02秒 / 0.31–0.47秒" },
      { label: "网页首帧亮度误差", value: "0.00133–0.00164 median luma" },
      { label: "网页首帧RGB MAE", value: "0.00617–0.01436", note: "复用已验证的sRGB JPEG与H.264代理；全部低于验收阈值0.025" },
      { label: "Live代理", value: "1280 × 960 · 24帧 · sRGB transfer" },
    ] : []),
  ],
}));

versions.push({
  version: "V25",
  year: "当前版本",
  title: "把观看条件与交换母版彻底分开",
  status: "current",
  projection: { src: "/versions/v25-t020-projection.jpg", label: "T020 · 2383影院观察的Rec.709监看" },
  bluray: { src: "/versions/v25-t020-bluray.jpg", label: "T020 · Period 2K / Rec.709蓝光" },
  summary: "V25不重新调5279颜色，也不改变V24的颗粒、MTF、DIR、2383或扫描完成曲线。第一次V25误把观看条件当成源文件编码：蓝光写入BT.1886反函数，放映监看又被重编码成P3 gamma 2.6，导致普通播放器中间调与暗部过亮。修正版把两份监看母版统一恢复为Rec.709 OETF与完整1-1-1；影院gamma和BT.1886只留在各自观察/显示端。固定种子条带与平均负片复用的无降质加速完整保留。",
  changes: ["修正第一次V25整体提亮的OETF/EOTF错位", "放映分支明确为2383影院观察的Rec.709监看呈现", "蓝光母版恢复Rec.709 OETF与完整1-1-1", "BT.1886只作为参考显示EOTF，不再反写进母版码值", "T020蓝光YAVG由1354.70回到1060.24，V24基线1060.04", "网页大图与Live视频从Rec.709母版统一转换到sRGB", "45组银盐位点固定种子并行与平均负片复用完整保留", "hourly研究只保留已通过官方来源与真实素材验证的结论"],
  errors: ["第一次V25把BT.1886显示EOTF的反函数直接作为蓝光源文件编码，同时仍标记为Rec.709 1-1-1，播放器解释后造成约20–28%的平均码值提亮", "第一次V25把已经经过影院→Rec.709监看适配的2383分支再次转换到P3 gamma 2.6，混合了物理影院观察器与监看交换母版", "P3色度、ST 428 transfer与BT.709 YUV矩阵混写在ProRes中，跨播放器行为不稳定", "参考显示标准不能替代交换信号定义；母版标签、OETF和网页解码必须端到端一致", "公开资料仍不足以识别5279所有层间参数；toe、DLE、Spirit窄带候选和rem-jet残余项因此没有进入V25"],
  discoveries: ["用户看到的提亮不是主观错觉：T020蓝光YLOW从304变成557，说明暗部被显著抬起", "BT.1886定义显示端V→L，不等于Rec.709交换母版必须直接使用其反函数", "2383_projection_monitor已经包含影院到监视器的观察适配，不能再次当作物理P3银幕信号编码", "固定随机条带让并行度与画面内容解耦：1和8线程的全画幅密度数组完全相同", "hourly研究的价值也包括证伪：LAD单点、未公开扫描器光谱或单通道专利数据不足以授权全局颜色变化"],
  refs: ["R1", "R4", "R26", "R27", "R28", "R29", "R30", "R31", "R32"],
  additionalTrials: [{
    name: "NJARAW_S001_S001_T032",
    note: "雨天青绿、暗柱与低反差纹理用于检查两个Rec.709监看分支的黑位、gamma和标签一致性。",
    projection: { src: "/versions/v25-t032-projection.jpg", label: "T032 · 2383影院观察的Rec.709监看" },
    bluray: { src: "/versions/v25-t032-bluray.jpg", label: "T032 · Period 2K / Rec.709蓝光" },
  }],
  parameters: v25Parameters,
});

const v25 = versions[versions.length - 1];
v25.year = "上一版";
v25.status = "calibration";

const v26Overrides: Record<string, string> = {
  "颜色决定": "V25修正基线完全锁定；V26不加入艺术调色",
  "显示编码": "Rec.709 OETF · 完整1-1-1 · 与V25修正版一致",
  "网页观察空间": "母版反Rec.709 OETF → sRGB IEC 61966-2-1",
};

const v26Parameters = (v25.parameters ?? []).map((group) => ({
  ...group,
  items: [
    ...group.items
      .filter((item) => group.title !== "数值验证与效率" || ![
        "V25修正一帧双母版", "V24等效一帧", "正式T020计时", "正式T032计时",
        "两段并行总等待", "相对V24总等待", "正式平均负片 / 帧", "正式乳剂形成 / 帧",
        "正式双观察器 / 帧", "错误版T020蓝光YAVG", "修正版T020蓝光YAVG", "错误→修正YLOW",
      ].includes(item.label))
      .map((item) => v26Overrides[item.label] ? { ...item, value: v26Overrides[item.label] } : item),
    ...(group.title === "乳剂颗粒" ? [
      { label: "快层五级权重", value: "0.12 · 0.26 · 0.34 · 0.20 · 0.08", note: "阴影/欠曝区以较大、较快晶体贡献为主" },
      { label: "中层五级权重", value: "0.16 · 0.30 · 0.32 · 0.17 · 0.05", note: "保持V24/V25已验证中心分布" },
      { label: "慢层五级权重", value: "0.22 · 0.34 · 0.29 · 0.12 · 0.03", note: "高光区减少大云尾部；不改变该记录48µm RMS" },
      { label: "时间模型", value: "每帧重新采样独立有限位点", note: "不移动、不循环、不平移一张噪点贴图" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "V26颜色/曲线变化", value: "无", note: "V25负片均值、MTF、DIR、2383、扫描器、黑位与Gamma全部锁定" },
      { label: "T020蓝光首帧YAVG", value: "V25 1060.24 → V26 1060.33", note: "变化0.09 / 4095；来自零均值随机实现" },
      { label: "T032蓝光首帧YAVG", value: "V25 1356.63 → V26 1356.73", note: "变化0.10 / 4095" },
      { label: "T020 / T032首帧YLOW", value: "304 / 281 · 与V25一致" },
      { label: "最大帧间lag-1相关", value: "0.0074", note: "均匀曝光四帧、三记录；接近独立随机场" },
      { label: "最大平均密度漂移", value: "0.00015 D", note: "四帧均匀曝光诊断；没有系统性色偏" },
      { label: "阴影快层颗粒功率", value: "约61–65%" },
      { label: "高光慢层颗粒功率", value: "约50–59%" },
      { label: "正式T020计时", value: "1894.14秒 · 31分34.14秒" },
      { label: "正式T032计时", value: "1893.93秒 · 31分33.93秒" },
      { label: "两段并行总等待", value: "1894.14秒 · 31分34.14秒" },
      { label: "平均负片 / 帧", value: "T020 36.60秒 · T032 36.64秒" },
      { label: "随机乳剂 / 帧", value: "18.17秒 · 19.21秒" },
      { label: "双观察器 / 帧", value: "21.66秒 · 20.11秒" },
      { label: "插件准备结论", value: "97%+核心时间适合GPU迁移", note: "Resolve 2026 OpenFX SDK已验证Metal/CUDA/OpenCL路径；当前参考实现仍是CPU" },
      { label: "输出", value: "两段各24帧 · 5760×4320 · 12-bit ProRes 4444 · 双母版" },
    ] : []),
  ],
}));

// V26/V27 hover loops are immutable, version-pinned website assets. Keeping
// them on the archival GitHub commit prevents two production hosts from
// packaging another 127 MiB while retaining the original pixels and URLs.
const archivedHover = (filename: string) =>
  `https://raw.githubusercontent.com/lovejzzz/90sKid/fa7152aed9552286220a798d602eb04d5797b824/public/versions/${filename}`;

versions.push({
  version: "V26",
  year: "当前版本",
  title: "让曝光选择颗粒频谱，而不是只改变颗粒响度",
  status: "current",
  projection: { src: "/versions/v26-t020-projection.jpg", videoSrc: archivedHover("v26-t020-projection-live-srgb.mp4"), label: "T020 · 2383影院观察的Rec.709监看" },
  bluray: { src: "/versions/v26-t020-bluray.jpg", videoSrc: archivedHover("v26-t020-bluray-live-srgb.mp4"), label: "T020 · Period 2K / Rec.709蓝光" },
  summary: "V26完全锁住V25修正版的色彩、黑位、对比、Gamma和Rec.709 1-1-1输出，只修正乳剂内部一个被简化的地方：快、中、慢三层不再共用同一套五级染料云权重。阴影由更大、更快的晶体统计主导，高光由更细的慢层主导；每个曝光和颜色记录仍重新回标5279公开的48µm扩散RMS，所以变化是颗粒空间频谱与有机运动，而不是更响的噪点。",
  changes: ["将五级染料云分布从全层共享改为快/中/慢三套权重", "阴影保留较宽的大云尾部，高光减少大云尾部", "每帧独立采样有限银盐位点，保持有机沸腾且不形成移动噪点贴图", "5279三记录48µm RMS继续作为最终振幅约束", "V25颜色、黑白灰、MTF、DIR、2383与Period 2K观察器逐项锁定", "首帧亮度和黑位数值回归通过", "加入NPS、层激活、均值漂移与帧间相关诊断", "T020与T032继续各交付1秒5.7K 12-bit双母版", "建立Resolve OFX迁移性能合同与Metal优先架构"],
  errors: ["V25的三速度层已有不同基础半径，但每层内部仍共用同一个五级尺寸分布", "共享分布会让慢层在高光中保留与快层相同的大云尾部，削弱35mm应有的曝光相关细腻变化", "仅用48µm RMS无法唯一决定颗粒观感；同一积分振幅可对应不同空间频谱", "5279没有公开逐亚层完整Wiener/NPS与涂布配方，因此V26权重是由Kodak机制约束的保守模型，不宣称是秘方复原"],
  discoveries: ["Kodak明确指出高速感光晶体通常最大，并在阴影或欠曝光处更明显", "三层噪声功率随p(1-p)而变化：阴影测试中快层约占61–65%，高光中慢层约占50–59%", "V26的高光有效颗粒半径下降，而阴影略向低频移动；总体48µm RMS不变", "四帧均匀场最大lag-1相关约0.0074，支持逐帧独立显影事件而非动画噪点", "T020/T032蓝光首帧YAVG相对V25仅变化0.09/0.10个12-bit码值，黑位不变"],
  refs: ["R1", "R7", "R21", "R23", "R25", "R33"],
  additionalTrials: [{
    name: "NJARAW_S001_S001_T032",
    note: "雨天青绿、暗柱、高光树叶与低反差纹理用于验证三速度层切换不会带来色相漂移或CCD式综合色噪点。",
    projection: { src: "/versions/v26-t032-projection.jpg", videoSrc: archivedHover("v26-t032-projection-live-srgb.mp4"), label: "T032 · 2383影院观察的Rec.709监看" },
    bluray: { src: "/versions/v26-t032-bluray.jpg", videoSrc: archivedHover("v26-t032-bluray-live-srgb.mp4"), label: "T032 · Period 2K / Rec.709蓝光" },
  }],
  parameters: v26Parameters,
});

const v26 = versions[versions.length - 1];
v26.year = "上一版";
v26.status = "calibration";

const groupTitlesEn: Record<string, string> = {
  "输入与母版": "INPUT & MASTERS",
  "5279乳剂": "5279 EMULSION",
  "5279乳剂与颗粒": "5279 EMULSION & GRAIN",
  "乳剂颗粒": "EMULSION GRAIN",
  "DIR显影耦合": "DIR DEVELOPMENT COUPLING",
  "2383放映链": "2383 PROJECTION CHAIN",
  "染料与2383放映": "DYES & 2383 PROJECTION",
  "显示器放映预览": "PROJECTION MONITOR VIEW",
  "Period 2K / 蓝光": "PERIOD 2K / BLU-RAY",
  "扫描与放映输出": "SCAN & PROJECTION OUTPUT",
  "数值验证与效率": "NUMERICAL VALIDATION & PERFORMANCE",
};

const parameterLabelsEn: Record<string, string> = {
  "源素材": "Source footage", "源素材 A": "Source A", "源素材 B": "Source B",
  "RAW解码": "RAW decode", "相机色彩": "Camera colour", "相机 / 记录": "Camera / record transform",
  "拍摄参数": "Capture settings", "虚拟曝光": "Virtual exposure", "画幅": "Frame", "画幅 / 帧率": "Frame / rate",
  "帧率": "Frame rate", "测试段": "Test segment", "每段长度": "Length per source", "母版": "Master",
  "显示编码": "Signal encoding", "片种": "Film stock", "片种 / 成像宽": "Stock / image width", "假定成像宽": "Assumed image width",
  "亚层结构": "Sublayer structure", "速度偏移": "Speed offsets", "容量比例 快/中/慢": "Capacity fast/mid/slow",
  "快层中心 R/G/B": "Fast centres R/G/B", "转折宽度 R/G/B": "Transition widths R/G/B",
  "ECD 青记录": "ECD cyan record", "ECD 品红记录": "ECD magenta record", "ECD 黄记录": "ECD yellow record",
  "颗粒校准孔径": "Grain calibration aperture", "颗粒校准": "Grain calibration", "颗粒相关尺度": "Grain correlation scale",
  "粒径占比": "Size fractions", "五级占比": "Five-class fractions", "粒径半径倍率": "Radius factors", "半径倍率": "Radius factors",
  "光学倍率": "Optical factors", "亚像素相位半径": "Subpixel phase radius", "相位步进": "Phase step",
  "光学σ 青记录": "Optical σ cyan", "光学σ 品红记录": "Optical σ magenta", "光学σ 黄记录": "Optical σ yellow",
  "有效位点 青记录": "Effective sites cyan", "有效位点 品红记录": "Effective sites magenta", "有效位点 黄记录": "Effective sites yellow",
  "负片MTF σ R/G/B": "Negative MTF σ R/G/B", "正片MTF σ R/G/B": "Print MTF σ R/G/B",
  "感色重叠 Row R": "Sensitivity overlap row R", "感色重叠 Row G": "Sensitivity overlap row G", "感色重叠 Row B": "Sensitivity overlap row B",
  "随机种子": "Random seed", "传感器噪声": "Sensor-noise treatment", "发生阶段": "Domain", "DIR阶段": "DIR domain",
  "扩散σ 快/中/慢": "Diffusion σ fast/mid/slow", "DIR扩散σ": "DIR diffusion σ", "层间强度": "Interlayer strength",
  "层内强度 R/G/B": "Intralayer strength R/G/B", "随机耦合": "Stochastic coupling",
  "释放增益 快/中/慢": "Release gain fast/mid/slow", "接收增益 快/中/慢": "Receiver gain fast/mid/slow",
  "传输矩阵 Row 1": "Transport matrix row 1", "传输矩阵 Row 2": "Transport matrix row 2", "传输矩阵 Row 3": "Transport matrix row 3",
  "中性约束": "Neutral constraint", "正片": "Print stock", "Status-A D-min R/G/B": "Status-A D-min R/G/B",
  "5279染料": "5279 dyes", "2383分析染料": "2383 analytical dyes",
  "LAD目标": "LAD aim", "LAD目标 / D-max": "LAD aim / D-max", "D-max": "D-max", "印片光": "Printer light",
  "放映光": "Projection light", "印片 / 放映光": "Printer / projection light", "Callier修正": "Callier correction",
  "典型影院flare": "Typical cinema flare", "层间矩阵 Row 1": "Interimage matrix row 1", "层间矩阵 Row 2": "Interimage matrix row 2", "层间矩阵 Row 3": "Interimage matrix row 3",
  "物理亮度权重": "Physical-lightness weight", "最大物理色相权重": "Maximum physical-hue weight", "最大物理饱和权重": "Maximum physical-saturation weight",
  "色度校准": "Chroma calibration", "显示色度校准": "Display chroma calibration", "校准格点": "Calibration lattice", "相对色度格点": "Relative-chroma lattice",
  "中性保护": "Neutral guard", "插值余量": "Interpolation margin", "扫描亮度锚点": "Scan-luma anchors", "目标亮度锚点": "Target-luma anchors",
  "色域映射": "Gamut mapping", "扫描观察器": "Scan observer", "扫描孔径": "Scan aperture", "Cineon": "Cineon mapping",
  "中性灰码值": "Neutral-gray code", "主色校正强度": "Primary-correction strength", "肩部释放": "Shoulder release",
  "蓝光下段gamma": "Blu-ray lower-scale gamma", "色度颗粒σ": "Chroma-grain σ", "色度颗粒σ / 高频": "Chroma grain σ / high-frequency retention",
  "高频色度保留": "High-frequency chroma retention", "硬件Grain Manager": "Hardware Grain Manager", "共享乳剂随机实现": "Shared emulsion realization",
  "颜色决定": "Colour decision", "放映缓存格点": "Projection cache lattice", "真实帧平均ΔE": "Real-frame mean ΔE", "真实帧p99 ΔE": "Real-frame p99 ΔE",
  "逐像素放映加速": "Per-pixel projection speed-up", "放映色度颗粒积分": "Projection chroma-grain integration", "颗粒平均色约束": "Grain mean-colour constraint",
  "V24 48µm RMS误差": "V24 48 µm RMS error", "T020综合色/明度颗粒": "T020 opponent/luma grain", "T032综合色/明度颗粒": "T032 opponent/luma grain",
  "V24平均颜色最大变化": "V24 maximum mean-colour change", "银盐采样 1→8线程": "Silver-site sampling, 1→8 workers", "线程一致性": "Worker invariance",
  "复用平均负片": "Mean-negative reuse", "颗粒质量捷径": "Grain quality shortcuts", "网页观察空间": "Web viewing space", "网页首帧亮度误差": "Web first-frame luma error",
  "网页首帧RGB MAE": "Web first-frame RGB MAE", "Live代理": "Live proxy", "放映监看母版": "Projection monitor master", "蓝光母版": "Blu-ray master",
  "影院观看条件": "Cinema viewing condition", "蓝光观看条件": "Blu-ray viewing condition", "母版范围": "Master range", "网页代理": "Web proxy",
  "V26颜色/曲线变化": "V26 colour / curve change", "T020蓝光首帧YAVG": "T020 Blu-ray first-frame YAVG", "T032蓝光首帧YAVG": "T032 Blu-ray first-frame YAVG",
  "T020 / T032首帧YLOW": "T020 / T032 first-frame YLOW", "最大帧间lag-1相关": "Maximum frame lag-1 correlation", "最大平均密度漂移": "Maximum mean-density drift",
  "阴影快层颗粒功率": "Shadow fast-layer grain power", "高光慢层颗粒功率": "Highlight slow-layer grain power",
  "快层五级权重": "Fast-layer five-class weights", "中层五级权重": "Medium-layer five-class weights", "慢层五级权重": "Slow-layer five-class weights", "时间模型": "Temporal model",
  "平均负片 / 帧": "Mean negative / frame", "随机乳剂 / 帧": "Stochastic emulsion / frame", "双观察器 / 帧": "Two observers / frame",
  "解码 / 双路编码 / 帧": "Decode / two encoders / frame",
  "插件准备结论": "Plugin readiness", "输出": "Output",
};

const exactValueEnglish: Record<string, string> = {
  "Panasonic官方RAW → V-Gamut": "Panasonic official RAW → V-Gamut",
  "Rec.709 OETF · 完整1-1-1 · 与V25修正版一致": "Rec.709 OETF · complete 1-1-1 · same as corrected V25",
  "R/G/B × 快/中/慢 × 5粒径": "R/G/B × fast/mid/slow × five size classes",
  "2.399963 rad · 黄金角": "2.399963 rad · golden angle",
  "逐帧、逐记录、逐速度群独立": "Independent per frame, record and speed population",
  "逐帧/记录/速度/粒径/固定条带；线程数不改变结果": "Independent per frame, record, speed, size class and fixed stripe; worker count does not change the result",
  "九亚层合并前的显影域": "Development domain before the nine sublayers merge",
  "均匀H-D严格不漂移": "Exact uniform H-D invariance",
  "D-min已扣除的带符号净光谱密度": "Signed net spectral density with D-min subtracted",
  "非线性Status-A积分反演": "Nonlinear inversion of integral Status-A density",
  "3200 K / Kodak氙灯SPD": "3200 K / Kodak xenon SPD",
  "D60相对Oklab a/b · L不变": "Relative D60 OKLab a/b · L unchanged",
  "Oklab恒色相压缩": "OKLab constant-hue compression",
  "V25修正基线完全锁定；V26不加入艺术调色": "Corrected V25 baseline fully locked; V26 adds no creative grade",
  "Spirit式宽带RGB · 620/540/470 nm": "Spirit-like broadband RGB · 620/540/470 nm",
  "只作用于signed delta；均值分支不变": "Signed delta only; deterministic mean branch unchanged",
  "σ 0.62 @ 2K · 高频0.36 · opponent 0.66": "σ 0.62 @ 2K · high-frequency 0.36 · opponent 0.66",
  "与V23完全相同（平均颜色链未改）": "Identical to V23 (mean-colour chain unchanged)",
  "放映1.58 → 0.93 · 扫描1.72 → 0.92": "Projection 1.58 → 0.93 · scan 1.72 → 0.92",
  "放映2.07 → 1.15 · 扫描2.11 → 1.08": "Projection 2.07 → 1.15 · scan 2.11 → 1.08",
  "0.000000（数值精确不变）": "0.000000 (numerically exact)",
  "45组全画幅有限位点二项采样": "45 full-frame finite-site binomial populations",
  "16核 / 48GB；采样时CPU约80%空闲": "16 cores / 48 GB; ~80% CPU idle during sampling",
  "第13帧静态图 = 短视频首帧": "Frame 13 still = live-preview first frame",
  "Rec.709-D65 OETF · 1-1-1": "Rec.709-D65 OETF · 1-1-1",
  "48 cd/m² · gamma 2.6（投影观察模型内部）": "48 cd/m² · gamma 2.6 (inside the projection observer)",
  "BT.1886 SDR参考显示": "BT.1886 SDR reference display",
  "full-range RGB计算 → 12-bit 4:4:4 ProRes": "Full-range RGB computation → 12-bit 4:4:4 ProRes",
  "5760×4320逐像素相同 · max Δ 0": "5760×4320 pixel-identical · max Δ 0",
  "删除每帧一次完整重复显影计算": "One duplicate full development pass removed per frame",
  "每帧重新采样独立有限位点": "Fresh independent finite-site sampling every frame",
  "97%+核心时间适合GPU迁移": "97%+ of core time is suitable for GPU migration",
  "两段各24帧 · 5760×4320 · 12-bit ProRes 4444 · 双母版": "24 frames per source · 5760×4320 · 12-bit ProRes 4444 · two masters",
};

const valueToEnglish = (value: string) => exactValueEnglish[value] ?? value
  .replaceAll("约", "~")
  .replaceAll("秒", "s")
  .replaceAll("分钟", "min")
  .replaceAll("分", "m")
  .replaceAll("帧", " frames")
  .replaceAll("两段各", "each of two sources: ")
  .replaceAll("无", "None")
  .replaceAll("是", "Yes")
  .replaceAll("与V25一致", "same as V25")
  .replaceAll("与V25修正版一致", "same as corrected V25");

const v27Parameters = (v26.parameters ?? []).map((group) => ({
  ...group,
  titleEn: groupTitlesEn[group.title] ?? group.title,
  items: [
    ...group.items
      .filter((item) => group.title !== "数值验证与效率" || ![
        "正式T020计时", "正式T032计时", "两段并行总等待", "平均负片 / 帧",
        "随机乳剂 / 帧", "双观察器 / 帧", "V26颜色/曲线变化",
      ].includes(item.label))
      .map((item) => ({
        ...item,
        labelEn: parameterLabelsEn[item.label] ?? item.label,
        valueEn: valueToEnglish(item.value),
      })),
    ...(group.title === "扫描与放映输出" ? [
      { label: "V27扫描灰轴", labelEn: "V27 scan gray axis", value: "2049级中性曝光 · 密度相关RGB平衡", valueEn: "2049-level neutral exposure scale · level-dependent RGB balance" },
      { label: "亮度约束", labelEn: "Luminance constraint", value: "逐像素Rec.709 Y严格保持", valueEn: "Exact per-pixel Rec.709 Y preservation", note: "不改变黑位、对比度、下段gamma或高光亮度", noteEn: "No change to black, contrast, lower-scale gamma or highlight luminance" },
      { label: "Period 2K孔径", labelEn: "Period 2K aperture", value: "与V26完全相同", valueEn: "Unchanged from V26" },
      { label: "2383放映母版", labelEn: "2383 projection master", value: "逐字节复用V26", valueEn: "Byte-identical reuse of V26" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "中性通道最大残差", labelEn: "Maximum neutral-channel residual", value: "0.01820 → 0.00236", valueEn: "0.01820 → 0.00236" },
      { label: "中性通道p95残差", labelEn: "p95 neutral-channel residual", value: "0.01673 → 0.00166", valueEn: "0.01673 → 0.00166" },
      { label: "绿色对手最大残差", labelEn: "Maximum green-opponent residual", value: "0.02172 → 0.00242", valueEn: "0.02172 → 0.00242" },
      { label: "最大亮度漂移", labelEn: "Maximum luminance drift", value: "1.79 × 10⁻⁷", valueEn: "1.79 × 10⁻⁷" },
      { label: "放映分支最大漂移", labelEn: "Maximum projection drift", value: "0.000000", valueEn: "0.000000" },
      { label: "Hourly研究进入模型", labelEn: "Hourly research entering model", value: "仅证据边界；不改颗粒、DIR或NPS", valueEn: "Evidence boundary only; no grain, DIR or NPS change" },
      { label: "正式T020扫描计时", labelEn: "Formal T020 scan time", value: "25分47.08秒", valueEn: "25m 47.08s", note: "末3帧与T032并行，计时包含母版定稿与静帧写入，不含随后SHA-256", noteEn: "Last three frames overlapped T032; includes master finalization and still export, excludes later SHA-256 hashing" },
      { label: "正式T032扫描计时", labelEn: "Formal T032 scan time", value: "25分09.09秒", valueEn: "25m 09.09s", note: "前3帧与T020并行，计时包含母版定稿与静帧写入，不含随后SHA-256", noteEn: "First three frames overlapped T020; includes master finalization and still export, excludes later SHA-256 hashing" },
      { label: "输出", labelEn: "Output", value: "两段各24帧 · 5760×4320 · 12-bit ProRes 4444 · 双母版", valueEn: "24 frames per source · 5760×4320 · 12-bit ProRes 4444 · two masters" },
    ] : []),
  ],
}));

versions.push({
  version: "V27",
  year: "当前版本",
  title: "把扫描器的绿色罩层从胶片颜色中分离出来",
  status: "current",
  projection: { src: "/versions/v27-t020-projection.jpg", videoSrc: archivedHover("v27-t020-projection-live-srgb.mp4"), label: "T020 · 2383影院观察的Rec.709监看（与V26相同）" },
  bluray: { src: "/versions/v27-t020-bluray.jpg", videoSrc: archivedHover("v27-t020-bluray-live-srgb.mp4"), label: "T020 · 中性灰阶约束的Period 2K / Rec.709蓝光" },
  summary: "V27确认V26蓝光版的朦胧绿色并非网页或颗粒造成，而是扫描观察器只在18%灰与一个高密度点校准后留下的密度相关灰轴误差。新版本以2049级中性曝光建立扫描RGB平衡，并逐像素恢复原Rec.709亮度，因此绿色残差下降，但黑位、对比、Gamma、2K孔径与高光亮度不动。V26负片、颗粒、DIR、2383和放映母版全部锁定。",
  changes: ["用完整中性曝光尺度替代扫描器的双锚点灰平衡", "在完成的Period 2K扫描分支中加入密度相关RGB校准", "逐像素保持Rec.709亮度，禁止校准变成调色", "中性通道最大残差从0.01820降至0.00236", "绿色对手残差从0.02172降至0.00242", "否决会让真实RAW更绿、更亮的完全主色分离方案", "V26颗粒、DIR、NPS、MTF、黑位和Gamma全部锁定", "2383放映母版逐字节复用V26", "结合最新hourly研究的不可识别性结论，不凭专利编号或48µm RMS发明新参数", "核对2003年5279临时专利原件：确认编号沿革，但仍无任何5279数值参数", "网站加入完整中英文切换并保存语言选择"],
  errors: ["V26扫描器只在18%灰和一个高密度点定标，无法保证整条灰阶中性", "V26人为保留18%的所谓Spirit/染料残余，但公开资料没有支持其色相和密度形状", "阴影和低中间调出现绿色隆起，中灰锚点正确，亮部偏移方向又改变，所以全局品红无法修复", "2K孔径的柔化与RGB灰轴错误曾在观感上混成同一种绿色雾感", "最新hourly研究仍没有公开5279专属NPS、DIR矩阵或Spirit私有校准，不能借V27改写这些部分"],
  discoveries: ["用户观察到的绿色罩层可以在中性尺度上重复测量", "网页Rec.709到sRGB转换对三通道一致，且放映版共用同一路径，因此不是网页ICC问题", "灰轴误差随密度改变方向，必须使用水平相关校准而不是一个白平衡旋钮", "保持每个像素的Rec.709 Y，可以把扫描色彩校准和艺术对比选择严格分开", "完全清除模拟扫描器串扰会改变亮度并让实拍植物更绿，说明更激进不等于更准确", "2003年4月临时专利确实把identifier 3写成5279；同年5月JVT-H022改成5218，后续专利又回到5279，属于文档分支漂移而不是胶片测量", "hourly研究的主要贡献是限制模型自由度：没有可识别证据的颗粒和DIR参数必须保持不变"],
  refs: ["R1", "R8", "R11", "R26", "R27", "R34", "R35", "R36", "R38", "R39", "R40", "R41"],
  additionalTrials: [{
    name: "NJARAW_S001_S001_T032",
    note: "雨天青绿、暗柱与低反差纹理用于确认灰轴校准不会把真实绿色错误拉回中性，也不会改变黑位和亮度。",
    projection: { src: "/versions/v27-t032-projection.jpg", videoSrc: archivedHover("v27-t032-projection-live-srgb.mp4"), label: "T032 · 2383影院观察的Rec.709监看（与V26相同）" },
    bluray: { src: "/versions/v27-t032-bluray.jpg", videoSrc: archivedHover("v27-t032-bluray-live-srgb.mp4"), label: "T032 · 中性灰阶约束的Period 2K / Rec.709蓝光" },
  }],
  parameters: v27Parameters,
});

const v27 = versions[versions.length - 1];
v27.year = "上一版";
v27.status = "calibration";

const v28Parameters = (v27.parameters ?? []).map((group) => ({
  ...group,
  items: [
    ...group.items
      .filter((item) => group.title !== "数值验证与效率" || ![
        "正式T020扫描计时", "正式T032扫描计时", "输出",
      ].includes(item.label))
      .map((item) => {
        if (item.label === "相机色彩") return {
          ...item,
          value: "Apple linear BT.2020 → XYZ D65 → Panasonic V-Gamut",
          valueEn: "Apple linear BT.2020 → XYZ D65 → Panasonic V-Gamut",
          note: "不再对已转换的BT.2020缓冲重复应用RAW-Gamut Camera LUT",
          noteEn: "No RAW-Gamut Camera LUT is reapplied to the converted BT.2020 buffer",
        };
        if (item.label === "2383放映母版") return {
          ...item,
          value: "由V28修正负片重新计算",
          valueEn: "Recomputed from the corrected V28 negative",
        };
        return item;
      }),
    ...(group.title === "输入与母版" ? [
      { label: "V28输入契约", labelEn: "V28 input contract", value: "AVFoundation extended-linear BT.2020 / D65", valueEn: "AVFoundation extended-linear BT.2020 / D65" },
      { label: "Camera LUT边界", labelEn: "Camera-LUT boundary", value: "仅RAW Gamut阶段可用；当前路径关闭", valueEn: "Valid only at RAW-Gamut stage; disabled in this path" },
      { label: "白平衡", labelEn: "White balance", value: "保留AVFoundation标准转换与as-shot元数据；不做第二次WB", valueEn: "Retain AVFoundation standard conversion and as-shot metadata; no second WB" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "T020扫描近中性G/R", labelEn: "T020 scan near-neutral G/R", value: "1.04294 → 1.02895", valueEn: "1.04294 → 1.02895" },
      { label: "T020放映近中性G/R", labelEn: "T020 projection near-neutral G/R", value: "1.00234 → 0.99971", valueEn: "1.00234 → 0.99971" },
      { label: "T032扫描近中性G/R", labelEn: "T032 scan near-neutral G/R", value: "1.06476 → 1.04777", valueEn: "1.06476 → 1.04777" },
      { label: "T032放映近中性G/R", labelEn: "T032 projection near-neutral G/R", value: "1.03915 → 1.02518", valueEn: "1.03915 → 1.02518" },
      { label: "高光验证", labelEn: "Highlight validation", value: "p99–p99.9基本不变 · 无白场裁切", valueEn: "p99–p99.9 essentially unchanged · no white clipping" },
      { label: "灰轴验证", labelEn: "Neutral-axis validation", value: "合成均匀灰完整管线保持中性", valueEn: "Synthetic uniform gray remains neutral through the full pipeline" },
      { label: "2383缓存", labelEn: "2383 cache", value: "193³分析格点 · SHA-256完整性校验", valueEn: "193³ analytical lattice · SHA-256 integrity check" },
      { label: "加速像素验证", labelEn: "Accelerated pixel validation", value: "两分支RGB48解码SHA-256逐位一致", valueEn: "Both branches are bit-identical by decoded RGB48 SHA-256" },
      { label: "正式T020双母版", labelEn: "Formal T020 dual masters", value: "979.19秒 · 16分19.19秒", valueEn: "979.19s · 16m 19.19s" },
      { label: "正式T032双母版", labelEn: "Formal T032 dual masters", value: "982.64秒 · 16分22.64秒", valueEn: "982.64s · 16m 22.64s" },
      { label: "两段并行总等待", labelEn: "Parallel wall time for both sources", value: "约982.64秒 · 16分22.64秒", valueEn: "~982.64s · 16m 22.64s" },
      { label: "T020每帧双母版", labelEn: "T020 dual masters per frame", value: "40.80秒", valueEn: "40.80s" },
      { label: "T032每帧双母版", labelEn: "T032 dual masters per frame", value: "40.94秒", valueEn: "40.94s" },
      { label: "输出", labelEn: "Output", value: "两段各24帧 · 5760×4320 · 12-bit ProRes 4444 · 双母版", valueEn: "24 frames per source · 5760×4320 · 12-bit ProRes 4444 · two masters" },
    ] : []),
  ],
}));

versions.push({
  version: "V28",
  year: "当前版本",
  title: "修正ProRes RAW解码与Panasonic Camera LUT的阶段边界",
  status: "current",
  projection: { src: "/versions/v28-t020-projection.jpg", videoSrc: "/versions/v28-t020-projection-live-srgb.mp4", label: "T020 · 修正输入契约后的2383影院观察Rec.709监看" },
  bluray: { src: "/versions/v28-t020-bluray.jpg", videoSrc: "/versions/v28-t020-bluray-live-srgb.mp4", label: "T020 · 修正输入契约后的Period 2K / Rec.709蓝光" },
  summary: "V28确认剩余绿色罩层的主要来源不是5279、Spirit灰轴或网页显示，而是RAW输入阶段次序：AVFoundation已经交付extended-linear BT.2020/D65，V27却把它再次当成Panasonic RAW Gamut送入Camera LUT。V28改为线性BT.2020→XYZ D65→V-Gamut的纯原色变换，不加入减绿、白平衡或创作调色；V27的负片曲线、染料、DIR、颗粒、黑位、对比、Gamma和观察器全部锁定。",
  changes: ["按Core Video附件确认解码缓冲为extended-linear BT.2020/D65", "删除已转换缓冲上的第二次RAW-Gamut Camera LUT解释", "使用线性BT.2020→XYZ D65→Panasonic V-Gamut原色变换", "保留AVFoundation标准ProRes RAW转换与as-shot元数据，不做第二次白平衡", "T020与T032的放映、扫描均从同一份修正负片重新计算", "黑位、对比、Gamma、高光与全部5279/2383参数保持V27", "2383完整分析格点加入SHA-256校验缓存与逐位一致的快速采样"],
  errors: ["V27误把已经是BT.2020原色的RGB缓冲当作Panasonic RAW Gamut", "RAW-Gamut Camera LUT是三维非线性相机分离，错位应用产生随场景变化的绿色与蓝色误差", "V27只修扫描灰轴，因此无法消除进入负片之前已经发生的颜色错误", "用全局品红、减饱和或lift/gamma掩盖问题会污染真实树林绿色并变成艺术调色"],
  discoveries: ["Camera LUT正确与否取决于输入处于哪一个阶段，而不只取决于文件来自哪台相机", "T032雨天树林本身确实偏青绿；正确模拟应去掉额外荧光绿罩，而不是把场景拉成中性", "修正后三个近中性比值下降，而p99–p99.9亮度与白场裁切基本不变", "合成均匀灰在完整V28链中保持中性，V27 Spirit中性校准仍然必要", "加速后的最终12-bit视频解码像素与参考实现逐位一致"],
  refs: ["R1", "R4", "R8", "R26", "R27", "R44", "R45", "R46", "R47"],
  additionalTrials: [{
    name: "NJARAW_S001_S001_T032",
    note: "雨天森林本身含有真实青绿色；这段素材用于区分场景色与错位Camera LUT产生的额外荧光绿罩。",
    projection: { src: "/versions/v28-t032-projection.jpg", videoSrc: "/versions/v28-t032-projection-live-srgb.mp4", label: "T032 · 修正输入契约后的2383影院观察Rec.709监看" },
    bluray: { src: "/versions/v28-t032-bluray.jpg", videoSrc: "/versions/v28-t032-bluray-live-srgb.mp4", label: "T032 · 修正输入契约后的Period 2K / Rec.709蓝光" },
  }],
  parameters: v28Parameters,
});

const v28 = versions[versions.length - 1];
v28.year = "上一版";
v28.status = "calibration";

const v29Parameters = (v28.parameters ?? []).map((group) => ({
  ...group,
  items: [
    ...group.items.filter((item) => {
      if (group.title === "输入与母版" && ["源素材 A", "源素材 B", "每段长度"].includes(item.label)) return false;
      if (group.title === "数值验证与效率" && [
        "正式T020双母版", "正式T032双母版", "两段并行总等待", "T020每帧双母版", "T032每帧双母版", "输出",
      ].includes(item.label)) return false;
      return true;
    }),
    ...(group.title === "输入与母版" ? [
      { label: "V29测试素材", labelEn: "V29 test source", value: "NJARAW_S001_S001_T002", valueEn: "NJARAW_S001_S001_T002" },
      { label: "原始视频", labelEn: "Source video", value: "165帧 · 6.881875秒 · 5760×4320 · 12-bit ProRes RAW HQ", valueEn: "165 frames · 6.881875s · 5760×4320 · 12-bit ProRes RAW HQ" },
      { label: "原始声音", labelEn: "Source audio", value: "24-bit PCM · 48 kHz · 4声道 · 无损保留", valueEn: "24-bit PCM · 48 kHz · 4 channels · stream copied" },
      { label: "时间码", labelEn: "Timecode", value: "12:04:05:23 · 原样保留", valueEn: "12:04:05:23 · retained" },
    ] : []),
    ...(group.title === "5279负片形成" ? [
      { label: "V29证据策略", labelEn: "V29 evidence policy", value: "没有片种专属测量，不改变NPS、DIR矩阵或三层配方", valueEn: "No stock-specific measurement, no change to NPS, DIR matrix or layer recipe" },
      { label: "时间随机性", labelEn: "Temporal stochasticity", value: "每个物理帧按绝对源帧号生成新的有限位点乳剂", valueEn: "A new finite-site emulsion keyed by absolute source-frame number" },
      { label: "分段边界", labelEn: "Segment boundary", value: "并行区段不重置、不重复、不平移颗粒", valueEn: "Parallel ranges do not reset, repeat or translate grain" },
    ] : []),
    ...(group.title === "数值验证与效率" ? [
      { label: "中性H-D门槛", labelEn: "Neutral H-D gate", value: "1025级最大误差 < 7×10⁻⁶ D", valueEn: "1025 levels · maximum error < 7×10⁻⁶ D" },
      { label: "均匀场DIR门槛", labelEn: "Uniform-field DIR gate", value: "每通道空间漂移 0.0 D", valueEn: "0.0 D spatial drift per record" },
      { label: "全运动验证", labelEn: "Full-motion validation", value: "逐帧黑场、高光、高频活动与时间相关性", valueEn: "Per-frame black, highlights, high-frequency activity and temporal correlation" },
      { label: "段落像素验证", labelEn: "Segment pixel gate", value: "全片第82帧与独立探针RGB48逐位完全相等", valueEn: "Full frame 82 and standalone probe are bit-exact equal in RGB48" },
      { label: "完整T002双母版", labelEn: "Complete T002 dual masters", value: "3113.17秒 · 51分53.17秒 · 两母版并行", valueEn: "3113.17s · 51m 53.17s · two masters in parallel" },
      { label: "双母版有效速度", labelEn: "Effective dual-master rate", value: "18.87秒/源帧", valueEn: "18.87s per source frame" },
      { label: "完整运动门槛", labelEn: "Full-motion gates", value: "165/165帧 · 白场硬截断0 · 验证通过", valueEn: "165/165 frames · zero hard white clipping · passed" },
      { label: "最终输出", labelEn: "Final output", value: "165帧 · 原始全长 · 5760×4320 · 12-bit ProRes 4444 · 双母版", valueEn: "165 frames · full source duration · 5760×4320 · 12-bit ProRes 4444 · two masters" },
    ] : []),
  ],
}));

versions.push({
  version: "V29",
  year: "当前基线",
  title: "从一秒样片进入完整运动验证：只实现证据允许的最后部分",
  status: "current",
  projection: { src: "/versions/v29-t002-projection.jpg", videoSrc: "/versions/v29-t002-projection-live-srgb.mp4", label: "T002 · 完整5279负片 → 2383影院观察Rec.709监看" },
  bluray: { src: "/versions/v29-t002-bluray.jpg", videoSrc: "/versions/v29-t002-bluray-live-srgb.mp4", label: "T002 · 完整5279负片 → Period 2K / Rec.709蓝光" },
  summary: "V29把剩余工作从主观“胶片味”转为可证伪验证。公开5279资料可以约束中性H-D、MTF和48µm RMS，却没有片种专属NPS、DIR矩阵、三层配方或Spirit光谱，因此这些未知参数保持V28。新版本完整渲染T002的165帧，让每一帧按绝对源帧号形成新的有限银盐位点/染料云场，检查真实运动中的黑场、高光、颗粒沸腾与分段接缝，并保留原始24-bit四声道声音和时间码。",
  changes: ["将T002全部165帧作为完整运动压力测试", "并行区段使用绝对源帧号种子，接缝不重置颗粒", "同一份逐帧乳剂同时生成2383与Period 2K观察结果", "加入全片黑场、高光、高频活动、时间相关性和段边界像素验证", "保留原始24-bit/48kHz四声道PCM和12:04:05:23时间码", "H-D、MTF、48µm RMS、色彩、黑位、Gamma和两观察器保持V28"],
  errors: ["不能把48µm单孔径RMS误称为完整颗粒NPS", "不能把Kodak专利中的示例扩散系数当成5279专属DIR矩阵", "不能把Spirit的公开硬件说明误称为专有光谱校准", "在没有实物对照时继续按单一场景调颗粒或颜色会把艺术选择混入baseline"],
  discoveries: ["最后15–20%中可用代码完成的是验证与交付；真正的片种识别需要新测量", "独立电影帧应形成新的乳剂马赛克，而不是移动或循环一张颗粒贴图", "并行加速可以保持绝对帧种子与输出像素一致", "完整运动比单帧更容易暴露闪烁、颗粒游泳、黑位偏置与高光不连续", "原音、时间码、色彩元数据和帧数也是行业标准母版的一部分"],
  refs: ["R1", "R3", "R7", "R8", "R21", "R22", "R23", "R25", "R34", "R35", "R36", "R37"],
  parameters: v29Parameters,
});

const v29 = versions[versions.length - 1];
v29.year = "上一版";
v29.status = "calibration";

const v30Parameters: ParameterGroup[] = [
  {
    title: "输入与母版", titleEn: "INPUT & MASTERS", items: [
      { label: "测试素材", labelEn: "Test sources", value: "T002 · T020 · T032", valueEn: "T002 · T020 · T032" },
      { label: "每段长度", labelEn: "Length per source", value: "24帧 · 1.001秒", valueEn: "24 frames · 1.001s" },
      { label: "RAW解码", labelEn: "RAW decode", value: "AVFoundation extended-linear BT.2020 / D65", valueEn: "AVFoundation extended-linear BT.2020 / D65" },
      { label: "虚拟曝光", labelEn: "Virtual exposure", value: "+0.45 stop · 三条链完全一致", valueEn: "+0.45 stop · identical for all three branches" },
      { label: "胶片母版", labelEn: "Film masters", value: "5760×4320 · 12-bit · ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 12-bit · ProRes 4444 · Rec.709 1-1-1" },
      { label: "相机基线", labelEn: "Camera baseline", value: "Panasonic官方V-Log→V-709 · 无5279/2383/扫描/调色", valueEn: "Official Panasonic V-Log→V-709 · no 5279/2383/scan/grade" },
      { label: "官方LUT SHA-256", labelEn: "Official LUT SHA-256", value: "f99223675b299339…a4578d", valueEn: "f99223675b299339…a4578d" },
    ],
  },
  {
    title: "5279乳剂与颗粒", titleEn: "5279 EMULSION & GRAIN", items: [
      { label: "负片模型", labelEn: "Negative model", value: "V29锁定：九亚层有限位点 · H-D · MTF · 48µm RMS", valueEn: "Locked V29: nine finite-site sublayers · H-D · MTF · 48 µm RMS" },
      { label: "颗粒形态", labelEn: "Grain morphology", value: "快/中/慢层独立五级多分散染料云", valueEn: "Independent five-class polydisperse dye clouds per fast/mid/slow layer" },
      { label: "时间随机性", labelEn: "Temporal stochasticity", value: "按绝对源帧号重新形成乳剂；不循环贴图", valueEn: "Fresh emulsion keyed by absolute source frame; no looping plate" },
      { label: "DIR", labelEn: "DIR", value: "九亚层反应–扩散 · 均匀场局部项归零", valueEn: "Nine-sublayer reaction–diffusion · local term vanishes on uniform fields" },
      { label: "V30颗粒变化", labelEn: "V30 grain change", value: "无", valueEn: "None", note: "没有新的5279专属NPS测量，不以三个场景主观调味", noteEn: "No new stock-specific NPS measurement; no scene-tuned flavour" },
    ],
  },
  {
    title: "2383放映链", titleEn: "2383 PROJECTION CHAIN", items: [
      { label: "Kodak LAD目标 R/G/B", labelEn: "Kodak LAD aims R/G/B", value: "1.09 / 1.06 / 1.03 D", valueEn: "1.09 / 1.06 / 1.03 D" },
      { label: "V29错误假设", labelEn: "V29 incorrect assumption", value: "相等LAD 1.00 / 1.00 / 1.00", valueEn: "Equal LAD 1.00 / 1.00 / 1.00" },
      { label: "D60供应商LUT强度", labelEn: "Vendor D60 LUT strength", value: "0", valueEn: "0", note: "不再把Resolve供应商LUT当作Kodak实测光谱", noteEn: "No longer treated as measured Kodak spectral evidence" },
      { label: "数字化染料曲线色相/饱和控制", labelEn: "Digitized dye-curve hue/saturation control", value: "0 / 0", valueEn: "0 / 0", note: "曲线保留作结构证据，不用未知扫描误差强迫最终色相", noteEn: "Retained as structural evidence, not a final hue authority" },
      { label: "分析LUT", labelEn: "Analytical LUT", value: "193³ · SHA-256 5a7d99c9e50a…f98c", valueEn: "193³ · SHA-256 5a7d99c9e50a…f98c" },
      { label: "投影观察", labelEn: "Projection observer", value: "2383氙灯 · 48 nit · gamma 2.6 → Rec.709监看", valueEn: "2383 xenon · 48 nit · gamma 2.6 → Rec.709 monitor view" },
    ],
  },
  {
    title: "Period 2K / 蓝光", titleEn: "PERIOD 2K / BLU-RAY", items: [
      { label: "扫描模型", labelEn: "Scan model", value: "V29逐像素不变 · 2K透射域孔径 · Cineon", valueEn: "Pixel-identical to V29 · 2K transmission aperture · Cineon" },
      { label: "完成态", labelEn: "Finishing", value: "Rec.709 1-1-1 · BT.1886仅作参考显示EOTF", valueEn: "Rec.709 1-1-1 · BT.1886 only as reference-display EOTF" },
      { label: "艺术调色", labelEn: "Creative grade", value: "无", valueEn: "None" },
    ],
  },
  {
    title: "数值验证与效率", titleEn: "NUMERICAL VALIDATION & PERFORMANCE", items: [
      { label: "统一验证", labelEn: "Unified validation", value: "通过 · failures 0", valueEn: "Passed · 0 failures" },
      { label: "近中性平均色度 T002/T020/T032", labelEn: "Near-neutral mean chroma T002/T020/T032", value: "0.00107 / 0.00455 / 0.00261", valueEn: "0.00107 / 0.00455 / 0.00261" },
      { label: "两观察器中位色相差", labelEn: "Median observer hue difference", value: "4.80° / 4.99° / 3.95°", valueEn: "4.80° / 4.99° / 3.95°" },
      { label: "T002双母版", labelEn: "T002 dual masters", value: "995.10秒 · 41.46秒/帧", valueEn: "995.10s · 41.46s/frame" },
      { label: "T020双母版", labelEn: "T020 dual masters", value: "997.60秒 · 41.57秒/帧", valueEn: "997.60s · 41.57s/frame" },
      { label: "T032双母版", labelEn: "T032 dual masters", value: "758.43秒 · 31.60秒/帧", valueEn: "758.43s · 31.60s/frame" },
      { label: "相机基线 T002/T020/T032", labelEn: "Camera baseline T002/T020/T032", value: "114.03 / 113.85 / 110.63秒", valueEn: "114.03 / 113.85 / 110.63s" },
      { label: "观察器线程", labelEn: "Observer workers", value: "1（安全默认）", valueEn: "1 (safe default)", note: "与双线程旧实现逐像素相同；避免Numba workqueue并发SIGABRT", noteEn: "Pixel-identical to the former two-thread result; avoids Numba workqueue SIGABRT" },
      { label: "T002相机白端", labelEn: "T002 camera white endpoint", value: "1.4%天空到达V-709白端", valueEn: "1.4% sky reaches the V-709 white endpoint", note: "发生在相机基线，不是5279肩部", noteEn: "Camera baseline behavior, not the 5279 shoulder" },
      { label: "网页代理", labelEn: "Web proxies", value: "同一第12帧 · sRGB静帧与24帧hover视频", valueEn: "Same frame 12 · sRGB still and 24-frame hover video" },
    ],
  },
];

versions.push({
  version: "V30",
  year: "上一基线",
  title: "用官方LAD校正2383色偏，并以三场景相机基线隔离胶片作用",
  status: "calibration",
  projection: { src: "/versions/v30-t002-projection.jpg", videoSrc: "/versions/v30-t002-projection-live-srgb.mp4", label: "T002 · 5279负片 → 2383影院观察Rec.709监看" },
  bluray: { src: "/versions/v30-t002-bluray.jpg", videoSrc: "/versions/v30-t002-bluray-live-srgb.mp4", label: "T002 · 5279负片 → Period 2K / Rec.709蓝光" },
  camera: { src: "/versions/v30-t002-camera.jpg", videoSrc: "/versions/v30-t002-camera-live-srgb.mp4", label: "T002 · Panasonic官方V-709相机基线 · 不进入胶片管线" },
  summary: "V30复查了放映版残留的蓝紫罩层。根因不是5279本身，而是V29把2383 LAD简化为相等RGB密度，又让第三方D60 LUT和未知误差的数字化染料曲线过度支配色相。V30改用Kodak H-61B公布的2383目标1.09/1.06/1.03 D，并把无法证明属于Kodak材料的色相与饱和控制归零。T002、T020、T032各以一秒原分辨率验证，同时增加仅经过Panasonic官方V-709显示转换的相机基线，以清楚区分原场景、5279负片、2383放映与时期扫描。",
  changes: ["使用Kodak H-61B的2383 LAD目标1.09/1.06/1.03 D", "移除供应商Resolve D60 LUT对Kodak物理色相的控制", "数字化净染料曲线不再强迫最终色相或饱和度", "T002/T020/T032各完成24帧原分辨率12-bit双母版", "每个例子加入Panasonic官方V-709相机基线", "九幅网页图与九段hover视频由同一第12帧、同一Rec.709→sRGB路径生成", "观察器改为安全顺序执行；结果与并行版逐像素一致", "加入近中性色度、观察器色相差、白端与完整格式门槛"],
  errors: ["V29错误使用相等LAD 1.00/1.00/1.00，忽略2383官方通道目标并形成蓝紫偏移", "第三方D60 LUT不是Kodak 2383实测光谱，不能作为物理颜色真值", "公开数据表曲线的数字化误差不足以授权高权重全局色相控制", "第一次相机基线把LUT的legal-range输出再次按legal编码，造成虚浮；已在发布前废弃", "两个Python观察线程同时进入Numba workqueue会触发SIGABRT；用户看到的Python退出来自这里"],
  discoveries: ["2383未处理感光乳剂中的蓝紫滤光染料会在冲洗中洗除，不能模拟成最终放映画面的均匀罩层", "扫描版相对更暖并不证明放映版应该绝对偏蓝；两条链必须分别检验中性轴", "官方不等LAD目标比主观减蓝更能解释并修正偏移", "T032原始雨天场景本身有青绿色与空气雾；相机基线可防止把场景色误当胶片错误", "顺序观察器在这台机器上避免线程争用且与并行结果逐像素相同", "原图对照必须经过必要的相机显示转换；灰色Log画面不是可用的原始参照"],
  refs: ["R1", "R2", "R3", "R4", "R26", "R27", "R48", "R49", "R50"],
  parameters: v30Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T020",
      note: "树皮、菌类、中性暗纹理与真实植被绿用于检验中性轴、暗部颜色和35mm颗粒尺度。",
      projection: { src: "/versions/v30-t020-projection.jpg", videoSrc: "/versions/v30-t020-projection-live-srgb.mp4", label: "T020 · 5279 → 2383影院观察Rec.709监看" },
      bluray: { src: "/versions/v30-t020-bluray.jpg", videoSrc: "/versions/v30-t020-bluray-live-srgb.mp4", label: "T020 · 5279 → Period 2K / Rec.709蓝光" },
      camera: { src: "/versions/v30-t020-camera.jpg", videoSrc: "/versions/v30-t020-camera-live-srgb.mp4", label: "T020 · Panasonic官方V-709相机基线" },
    },
    {
      name: "NJARAW_S001_S001_T032",
      note: "雨天青绿树林、空气雾与低反差细节用于区分真实场景色、相机显示与胶片观察器偏移。",
      projection: { src: "/versions/v30-t032-projection.jpg", videoSrc: "/versions/v30-t032-projection-live-srgb.mp4", label: "T032 · 5279 → 2383影院观察Rec.709监看" },
      bluray: { src: "/versions/v30-t032-bluray.jpg", videoSrc: "/versions/v30-t032-bluray-live-srgb.mp4", label: "T032 · 5279 → Period 2K / Rec.709蓝光" },
      camera: { src: "/versions/v30-t032-camera.jpg", videoSrc: "/versions/v30-t032-camera-live-srgb.mp4", label: "T032 · Panasonic官方V-709相机基线" },
    },
  ],
});

const v30 = versions[versions.length - 1];
v30.year = "上一版";
v30.status = "calibration";

const v32Parameters: ParameterGroup[] = [
  {
    title: "输入与冻结边界", titleEn: "INPUT & FROZEN BOUNDARY", items: [
      { label: "独立测试素材", labelEn: "Independent sources", value: "T007 · T031", valueEn: "T007 · T031" },
      { label: "采样范围", labelEn: "Source ranges", value: "T007 276–299 · T031 132–155", valueEn: "T007 276–299 · T031 132–155" },
      { label: "每段长度", labelEn: "Length per source", value: "24帧 · 1.001秒", valueEn: "24 frames · 1.001s" },
      { label: "源格式", labelEn: "Source format", value: "GH7 / Atomos · ProRes RAW HQ 12-bit · 5760×4320", valueEn: "GH7 / Atomos · ProRes RAW HQ 12-bit · 5760×4320" },
      { label: "逐镜头调节", labelEn: "Per-shot tuning", value: "无", valueEn: "None" },
      { label: "相对V31图像变化", labelEn: "Image change from V31", value: "无 · 全部成像参数冻结", valueEn: "None · all image-forming parameters frozen" },
    ],
  },
  {
    title: "四种观察与交付", titleEn: "FOUR OBSERVATIONS & DELIVERIES", items: [
      { label: "相机基线", labelEn: "Camera baseline", value: "Panasonic官方V-709 · 不进入胶片管线", valueEn: "Official Panasonic V-709 · no film pipeline" },
      { label: "2383放映监看", labelEn: "2383 projection monitor", value: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1" },
      { label: "时期2K扫描", labelEn: "Period 2K scan", value: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1" },
      { label: "影院标准序列", labelEn: "Cinema-standard sequence", value: "2880×2160 · 24fps · ST 428-1 12-bit X′Y′Z′ DCDM TIFF", valueEn: "2880×2160 · 24fps · ST 428-1 12-bit X′Y′Z′ DCDM TIFF" },
      { label: "DCP状态", labelEn: "DCP status", value: "未封装 · DCDM是JPEG 2000 / MXF之前的无损检验序列", valueEn: "Unpackaged · lossless DCDM test sequence before JPEG 2000 / MXF" },
    ],
  },
  {
    title: "V31图像形成冻结", titleEn: "V31 IMAGE FORMATION LOCK", items: [
      { label: "5279负片", labelEn: "5279 negative", value: "九亚层、五粒径、三记录H-D曲线不变", valueEn: "Nine sublayers, five size classes and three record H-D curves unchanged" },
      { label: "局部效应", labelEn: "Local effects", value: "DIR、染料云扩散、MTF不变", valueEn: "DIR, dye-cloud diffusion and MTF unchanged" },
      { label: "2383", labelEn: "2383", value: "LAD 1.09/1.06/1.03 D · 明暗与颗粒不变", valueEn: "LAD 1.09/1.06/1.03 D · tone and grain unchanged" },
      { label: "正常工艺边界", labelEn: "Normal-process boundary", value: "无残余银、skip bleach、ENR或艺术调色", valueEn: "No retained silver, skip bleach, ENR or creative grade" },
      { label: "V31综合色度规则", labelEn: "V31 chroma rule", value: "扫描低频a/b + 放映高频综合色残差；逐像素Y保持", valueEn: "Scan low-frequency a/b + projection high-frequency opponent residual; per-pixel Y preserved" },
    ],
  },
  {
    title: "测量门槛与OFX迁移", titleEn: "MEASUREMENT GATES & OFX MIGRATION", items: [
      { label: "格式门槛", labelEn: "Format gate", value: "24帧 · 5.7K · ProRes 4444 · 12-bit · Rec.709 1-1-1", valueEn: "24 frames · 5.7K · ProRes 4444 · 12-bit · Rec.709 1-1-1" },
      { label: "时序门槛", labelEn: "Temporal gates", value: "均值、p99、硬裁切、纹理功率、中性轴逐帧检测", valueEn: "Frame-wise mean, p99, hard clip, texture power and neutral axis" },
      { label: "DCDM回环", labelEn: "DCDM round trip", value: "X′Y′Z′ → 线性Rec.709 p99误差 < 0.003", valueEn: "X′Y′Z′ → linear Rec.709 p99 error < 0.003" },
      { label: "OFX区域契约", labelEn: "OFX region contract", value: "σ=0.72×宽/2048 · halo=ceil(6σ)", valueEn: "σ=0.72×width/2048 · halo=ceil(6σ)" },
      { label: "调度规则", labelEn: "Scheduling rule", value: "宿主调度帧 · 随机种子取绝对源帧号", valueEn: "Host-scheduled frames · random seed uses absolute source-frame index" },
      { label: "质量策略", labelEn: "Quality policy", value: "GPU未通过数值与统计同一性前，以Archive Exact为准", valueEn: "Archive Exact remains authoritative until GPU numerical/statistical parity passes" },
    ],
  },
  {
    title: "实测效率", titleEn: "MEASURED PERFORMANCE", items: [
      { label: "T031双母版核心", labelEn: "T031 dual-master core", value: "589.25秒 · 24.55秒/源帧（两母版合计）", valueEn: "589.25s · 24.55s/source frame for both masters" },
      { label: "T007双母版核心", labelEn: "T007 dual-master core", value: "668.79秒 · 27.87秒/源帧（两母版合计）", valueEn: "668.79s · 27.87s/source frame for both masters" },
      { label: "主要瓶颈", labelEn: "Primary bottleneck", value: "随机乳剂约18–21秒/帧/worker；观察器约15–17秒/帧/worker", valueEn: "Stochastic emulsion ≈18–21s/frame/worker; observers ≈15–17s/frame/worker" },
      { label: "编码占比", labelEn: "Encoding share", value: "约0.38–0.58秒/帧/worker · 不是主要瓶颈", valueEn: "≈0.38–0.58s/frame/worker · not the primary bottleneck" },
      { label: "T031 DCDM", labelEn: "T031 DCDM", value: "23.56秒 · 0.97秒/帧", valueEn: "23.56s · 0.97s/frame" },
      { label: "T007 DCDM", labelEn: "T007 DCDM", value: "13.55秒 · 0.56秒/帧", valueEn: "13.55s · 0.56s/frame" },
      { label: "统一验证", labelEn: "Unified validation", value: "通过 · 2场景 · failures 0", valueEn: "Passed · 2 scenes · 0 failures" },
    ],
  },
];

versions.push({
  version: "V32",
  year: "当前基线",
  title: "冻结被认可的画面，把下一步从观感判断变成可重复测量",
  status: "current",
  projection: { src: "/versions/v32-t007-projection.jpg", videoSrc: "/versions/v32-t007-projection-live-srgb.mp4", label: "T007 · V31正常5279 → 2383影院观察 · V32测量验证" },
  bluray: { src: "/versions/v32-t007-bluray.jpg", videoSrc: "/versions/v32-t007-bluray-live-srgb.mp4", label: "T007 · V31 5279 → Period 2K扫描 · V32测量验证" },
  camera: { src: "/versions/v32-t007-camera.jpg", videoSrc: "/versions/v32-t007-camera-live-srgb.mp4", label: "T007 · Panasonic官方V-709相机基线" },
  summary: "V32不改变V31的任何画面参数。它用两段全新GH7 ProRes RAW素材，在没有逐镜头调节的前提下复验5279乳剂、正常2383放映与时期2K扫描；并把原生格式、亮度保持、高光裁切、时序纹理、中性轴、OFX分块区域和影院X′Y′Z′交付写成自动门槛。V32因此不是一次新的look，而是把目前可信的look变成可以迁移、复现和否证的基线。",
  changes: ["T007与T031各新增24帧原分辨率独立场景验证", "V31所有图像形成参数冻结，无逐镜头颜色、曝光、颗粒或对比调整", "逐帧检测亮度、p99高光、硬裁切、纹理功率和近中性a/b漂移", "加入SMPTE ST 428-1 12-bit X′Y′Z′ DCDM无损影院检验序列", "明确否决P3-D65/gamma 2.6 ProRes运输实验，避免MOV/ProRes/播放器元数据歧义", "加入OFX tile/ROI数值同一性契约，为Resolve插件迁移做准备", "逐阶段计时证明瓶颈位于随机乳剂与观察器，而不是ProRes编码"],
  errors: ["早期P3 ProRes探针同时依赖RGB含义、MOV色彩原子和播放器解释；这重复了V25已经发现的跨播放器不确定性，因此未列为交付", "用缩小后的网页预览做DCDM回环会混入二次缩放误差；最终验证直接解码原分辨率第12帧后再按同一面积核缩放", "第一次T007 V31边界试跑把输出目录误传为文件名，编码器立即拒绝；未产生有效画面，修正路径后重新完整运行"],
  discoveries: ["当画面已达到可信状态，最有价值的下一步可能是冻结而不是继续调色", "同一算法在水面高光、细草与暖色菌类上无需逐镜头调节，是比单帧好看更强的证据", "DCDM可以完整保存当前放映观察的外观，但不会凭空扩大原Rec.709监看中已经裁掉的色域", "两路12-bit母版并行生成时，随机乳剂与光谱观察器主导时间；编码只占很小部分", "插件分块的halo必须由完整输出宽度决定，否则代理尺寸和tile宽度会暗中改变颜色/颗粒交叉尺度"],
  refs: ["R26", "R28", "R32", "R44", "R49", "R53"],
  parameters: v32Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T031",
      note: "中性石面、暖色菌类、苔藓和暗部叶片检验灰轴、综合色度与高频纹理是否跨场景稳定。",
      projection: { src: "/versions/v32-t031-projection.jpg", videoSrc: "/versions/v32-t031-projection-live-srgb.mp4", label: "T031 · 正常5279 → 2383影院观察" },
      bluray: { src: "/versions/v32-t031-bluray.jpg", videoSrc: "/versions/v32-t031-bluray-live-srgb.mp4", label: "T031 · 5279 → Period 2K扫描" },
      camera: { src: "/versions/v32-t031-camera.jpg", videoSrc: "/versions/v32-t031-camera-live-srgb.mp4", label: "T031 · Panasonic官方V-709相机基线" },
    },
  ],
});

const v31Parameters: ParameterGroup[] = [
  {
    title: "输入与母版", titleEn: "INPUT & MASTERS", items: [
      { label: "测试素材", labelEn: "Test sources", value: "T002 · T020 · T032", valueEn: "T002 · T020 · T032" },
      { label: "每段长度", labelEn: "Length per source", value: "24帧 · 1.001秒", valueEn: "24 frames · 1.001s" },
      { label: "RAW与虚拟曝光", labelEn: "RAW & virtual exposure", value: "AVFoundation linear BT.2020 / D65 · +0.45 stop", valueEn: "AVFoundation linear BT.2020 / D65 · +0.45 stop" },
      { label: "母版", labelEn: "Masters", value: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 12-bit ProRes 4444 · Rec.709 1-1-1" },
      { label: "相机基线", labelEn: "Camera baseline", value: "V30逐像素沿用 · Panasonic官方V-709", valueEn: "Pixel-identical V30 baseline · official Panasonic V-709" },
    ],
  },
  {
    title: "正常工艺边界", titleEn: "NORMAL-PROCESS BOUNDARY", items: [
      { label: "负片处理", labelEn: "Negative process", value: "正常ECN-2 · 显影银影经漂白/定影移除", valueEn: "Normal ECN-2 · developed silver removed by bleach/fix" },
      { label: "正片处理", labelEn: "Print process", value: "正常ECP-2D · 画面银影经漂白/定影移除", valueEn: "Normal ECP-2D · picture silver removed by bleach/fix" },
      { label: "残余银项", labelEn: "Residual-silver term", value: "无", valueEn: "None" },
      { label: "留银/ENR/skip bleach", labelEn: "Bypass / ENR / skip bleach", value: "不属于baseline；未来必须独立建模", valueEn: "Outside baseline; requires a separate future model" },
    ],
  },
  {
    title: "5279乳剂与质感", titleEn: "5279 EMULSION & TEXTURE", items: [
      { label: "负片、DIR、MTF", labelEn: "Negative, DIR, MTF", value: "V30逐项锁定", valueEn: "Locked to V30" },
      { label: "九亚层与五级粒径", labelEn: "Nine sublayers / five size classes", value: "V30逐项锁定", valueEn: "Locked to V30" },
      { label: "48µm RMS回标", labelEn: "48 µm RMS calibration", value: "不变", valueEn: "Unchanged" },
      { label: "投影亮度/综合色纹理", labelEn: "Projection luma/opponent texture", value: "不变", valueEn: "Unchanged" },
      { label: "V31颗粒变化", labelEn: "V31 grain change", value: "无", valueEn: "None", note: "用户认可的V30质感完整保留", noteEn: "The accepted V30 texture is retained" },
    ],
  },
  {
    title: "2383综合色度—明暗适配", titleEn: "2383 CHROMA / TONE ADAPTATION", items: [
      { label: "Kodak LAD目标 R/G/B", labelEn: "Kodak LAD aims R/G/B", value: "1.09 / 1.06 / 1.03 D", valueEn: "1.09 / 1.06 / 1.03 D" },
      { label: "V30阶段错误", labelEn: "V30 stage error", value: "保持C/L；L下降时绝对综合色度C被同步抽走", valueEn: "Preserved C/L; lower L automatically removed absolute C" },
      { label: "V31阶段规则", labelEn: "V31 stage rule", value: "扫描低频OKLab a/b + 放映高频综合色残差", valueEn: "Scan low-frequency OKLab a/b + projection high-frequency opponent residual" },
      { label: "频率交叉", labelEn: "Frequency crossover", value: "σ=0.72px @ 2K · 沿用V24扫描综合色孔径", valueEn: "σ=0.72 px @ 2K · inherited V24 scan opponent aperture" },
      { label: "明暗保护", labelEn: "Luma protection", value: "逐像素线性Rec.709 Y保持 · 围绕Y压缩色域", valueEn: "Exact per-pixel linear Rec.709 Y · gamut compressed around Y" },
      { label: "艺术饱和度", labelEn: "Creative saturation", value: "无", valueEn: "None" },
      { label: "基准投影LUT", labelEn: "Baseline projection LUT", value: "V30锁定 · 193³ · SHA-256 5a7d99c9…f98c", valueEn: "Locked V30 · 193³ · SHA-256 5a7d99c9…f98c" },
    ],
  },
  {
    title: "验证与效率", titleEn: "VALIDATION & PERFORMANCE", items: [
      { label: "V30诊断 · 放映综合色度", labelEn: "V30 diagnostic · projection chroma", value: "比扫描低约12–17%", valueEn: "About 12–17% below the scan" },
      { label: "V30诊断 · 明暗跨度", labelEn: "V30 diagnostic · luma span", value: "比扫描高约27–32%", valueEn: "About 27–32% above the scan" },
      { label: "V30诊断 · 亮度纹理", labelEn: "V30 diagnostic · luma texture", value: "比扫描高约48–60%", valueEn: "About 48–60% above the scan" },
      { label: "T002双母版", labelEn: "T002 dual masters", value: "778.76秒 · 32.45秒/帧", valueEn: "778.76s · 32.45s/frame" },
      { label: "T020双母版", labelEn: "T020 dual masters", value: "764.84秒 · 31.87秒/帧", valueEn: "764.84s · 31.87s/frame" },
      { label: "T032双母版", labelEn: "T032 dual masters", value: "784.62秒 · 32.69秒/帧", valueEn: "784.62s · 32.69s/frame" },
      { label: "V31最终边界 T002/T020/T032", labelEn: "V31 final boundary T002/T020/T032", value: "101.22 / 100.35 / 101.68秒", valueEn: "101.22 / 100.35 / 101.68s" },
      { label: "最终边界速度", labelEn: "Final-boundary speed", value: "约4.14秒/帧", valueEn: "About 4.14s/frame" },
      { label: "放映/扫描综合色度保持", labelEn: "Projection/scan chroma retention", value: "91.1 / 93.3 / 89.2%", valueEn: "91.1 / 93.3 / 89.2%" },
      { label: "放映/扫描综合色饱和度", labelEn: "Projection/scan chroma saturation", value: "103.5 / 96.7 / 96.6%", valueEn: "103.5 / 96.7 / 96.6%" },
      { label: "V30亮度细纹理保持", labelEn: "V30 fine-luma texture retained", value: "99.2 / 98.9 / 99.1%", valueEn: "99.2 / 98.9 / 99.1%" },
      { label: "扫描回归", labelEn: "Scan regression", value: "三段均与V30 SHA-256完全相同", valueEn: "All three SHA-256-identical to V30" },
      { label: "统一验证", labelEn: "Unified validation", value: "通过 · failures 0", valueEn: "Passed · 0 failures" },
      { label: "统一参数", labelEn: "Unified parameters", value: "三场景无逐镜头调节", valueEn: "No per-scene tuning" },
    ],
  },
];

versions.push({
  version: "V31",
  year: "当前基线",
  title: "解除2383综合色度与明暗的错误耦合，让正常工艺不再意外接近留银",
  status: "current",
  projection: { src: "/versions/v31-t002-projection.jpg", videoSrc: "/versions/v31-t002-projection-live-srgb.mp4", label: "T002 · 正常5279 → 2383影院观察Rec.709监看" },
  bluray: { src: "/versions/v31-t002-bluray.jpg", videoSrc: "/versions/v31-t002-bluray-live-srgb.mp4", label: "T002 · 5279 → Period 2K / Rec.709蓝光" },
  camera: { src: "/versions/v31-t002-camera.jpg", videoSrc: "/versions/v31-t002-camera-live-srgb.mp4", label: "T002 · Panasonic官方V-709相机基线 · 不进入胶片管线" },
  summary: "V31回应V30放映版类似《拯救大兵瑞恩》留银观感的问题。正常ECN-2与ECP-2D会漂白并定影移除画面银影；V30没有残余银项，却在Rec.709放映适配中保持C/L，使更陡的2383明暗曲线在压低L时同步抽走绝对综合色度C，再与强烈亮度颗粒组合成轻度bleach-bypass判别特征。V31保持V30的5279、颗粒、DIR、MTF、黑位、Gamma、2383 LAD与亮度曲线，在最终成片边界用Period 2K观察器提供低频染料颜色，并保留放映链自己的高频综合色颗粒与逐像素亮度。它不是增艳，也不是艺术调色。",
  changes: ["正常ECN-2/ECP-2D基线明确排除残余银、skip bleach、ENR与bleach bypass", "最终成片域分离低频染料颜色与高频综合色颗粒", "Period 2K提供低频OKLab a/b；2383保留高频opponent残差", "逐像素保持V30线性Rec.709亮度，并围绕目标Y压缩色域", "V30官方2383 LAD 1.09/1.06/1.03 D完整保留", "5279负片、九亚层颗粒、DIR、MTF、黑位、Gamma和投影亮度纹理不变", "T002/T020/T032各以24帧原分辨率12-bit验证", "扫描母版与V30逐文件SHA-256回归"],
  errors: ["V30声称分离tone与colour，却把综合色度保存为C/L；替换L后并没有真正保持colour", "第一次V31实现只改缓存内适配，但旧物理/校准混合支路绕过了它，整片被验证拒绝", "第二次探针只校正确定性均值，随后被颗粒均值保持阶段拉回V30，再次被拒绝", "最终修正必须位于两条完整观察器之后，才能同时看见真实成片颜色与颗粒", "不能用全局加饱和或抬黑修复；那会把艺术调色混入baseline"],
  discoveries: ["留银观感可以由显示适配阶段产生，即使化学模型里没有残余银", "综合色度与饱和度不是同一量：保持C/L不等于在改变L时保持染料综合色度", "正常漂白工艺是baseline的可证伪边界，而不只是一个风格偏好", "未来留银toggle必须显式加入残余银密度并重新通过印片/扫描观察器", "用户喜欢的有机质感来自既有乳剂和亮度纹理，不需要牺牲来修正颜色"],
  refs: ["R3", "R4", "R48", "R51", "R52"],
  parameters: v31Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T020",
      note: "树皮与菌类检验暗部绝对综合色度是否在保持密度结构时仍然存在。",
      projection: { src: "/versions/v31-t020-projection.jpg", videoSrc: "/versions/v31-t020-projection-live-srgb.mp4", label: "T020 · 正常5279 → 2383影院观察Rec.709监看" },
      bluray: { src: "/versions/v31-t020-bluray.jpg", videoSrc: "/versions/v31-t020-bluray-live-srgb.mp4", label: "T020 · V30逐像素不变的Period 2K扫描" },
      camera: { src: "/versions/v31-t020-camera.jpg", videoSrc: "/versions/v31-t020-camera-live-srgb.mp4", label: "T020 · Panasonic官方V-709相机基线" },
    },
    {
      name: "NJARAW_S001_S001_T032",
      note: "雨天青绿和空气雾检验综合色度恢复不会把真实场景色中和或转暖。",
      projection: { src: "/versions/v31-t032-projection.jpg", videoSrc: "/versions/v31-t032-projection-live-srgb.mp4", label: "T032 · 正常5279 → 2383影院观察Rec.709监看" },
      bluray: { src: "/versions/v31-t032-bluray.jpg", videoSrc: "/versions/v31-t032-bluray-live-srgb.mp4", label: "T032 · V30逐像素不变的Period 2K扫描" },
      camera: { src: "/versions/v31-t032-camera.jpg", videoSrc: "/versions/v31-t032-camera-live-srgb.mp4", label: "T032 · Panasonic官方V-709相机基线" },
    },
  ],
});

const v31 = versions.find((item) => item.version === "V31");
if (v31) {
  v31.year = "上一版";
  v31.status = "calibration";
}
const v32Index = versions.findIndex((item) => item.version === "V32");
const [v32] = versions.splice(v32Index, 1);
v32.year = "当前基线";
v32.status = "current";
versions.push(v32);

const v33Parameters: ParameterGroup[] = [
  {
    title: "相机输入与曝光边界", titleEn: "CAMERA INPUT & EXPOSURE BOUNDARY", items: [
      { label: "As Shot见证", labelEn: "As Shot witness", value: "Panasonic V-709 · 0.00 stop · 不进入胶片管线", valueEn: "Panasonic V-709 · 0.00 stop · no film pipeline" },
      { label: "虚拟胶片EI", labelEn: "Virtual film EI", value: "+0.45 stop · 显式参数", valueEn: "+0.45 stop · explicit parameter" },
      { label: "自动去绿", labelEn: "Automatic green neutralization", value: "关闭", valueEn: "Disabled", note: "等待同光源灰卡/ColorChecker实测；不使用gray-world", noteEn: "Awaiting same-light gray-card/ColorChecker measurement; no gray-world correction" },
      { label: "校正位置", labelEn: "Correction location", value: "若被实测授权，仅在5279之前的相机输入边界", valueEn: "If measurement authorizes it: camera input, before 5279 only" },
      { label: "FCP见证", labelEn: "FCP witness", value: "T031源帧144 · Standard/as-shot · SHA-256 612077c7…aa88", valueEn: "T031 source frame 144 · Standard/as-shot · SHA-256 612077c7…aa88" },
    ],
  },
  {
    title: "黑场、Toe与Gamma", titleEn: "BLACK, TOE & GAMMA", items: [
      { label: "硬黑定义", labelEn: "Display-black definition", value: "Rec.709编码亮度 ≤ 1/1023", valueEn: "Rec.709 encoded luma ≤ 1/1023" },
      { label: "放映硬黑 T002/T007/T031", labelEn: "Projection black T002/T007/T031", value: "0.00095% / 0% / 0.00133%", valueEn: "0.00095% / 0% / 0.00133%" },
      { label: "扫描硬黑 T002/T007/T031", labelEn: "Scan black T002/T007/T031", value: "1.820% / 0.0133% / 1.349%", valueEn: "1.820% / 0.0133% / 1.349%" },
      { label: "放映有效log-luma power", labelEn: "Projection effective log-luma power", value: "1.352 / 1.373 / 1.351", valueEn: "1.352 / 1.373 / 1.351" },
      { label: "扫描有效log-luma power", labelEn: "Scan effective log-luma power", value: "1.514 / 1.343 / 1.504", valueEn: "1.514 / 1.343 / 1.504" },
      { label: "32级稳健色调映射", labelEn: "32-bin robust tone mapping", value: "两观察器 · 三场景 · 负向步数0", valueEn: "Both observers · three scenes · 0 negative steps" },
    ],
  },
  {
    title: "母版与稳定性契约", titleEn: "MASTER & STABILITY CONTRACT", items: [
      { label: "图像变化", labelEn: "Image change", value: "无 · V31/V32成像母版逐字节冻结", valueEn: "None · accepted V31/V32 image masters byte-frozen" },
      { label: "三段素材", labelEn: "Three sources", value: "T002 0–23 · T007 276–299 · T031 132–155", valueEn: "T002 0–23 · T007 276–299 · T031 132–155" },
      { label: "母版", labelEn: "Masters", value: "5760×4320 · 24帧 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 24 frames · 12-bit ProRes 4444 · Rec.709 1-1-1" },
      { label: "部分区间音频", labelEn: "Partial-range audio", value: "PCM采样级atrim · 24帧测试=48048 samples", valueEn: "Sample-accurate PCM atrim · 24-frame test=48,048 samples" },
      { label: "部分区间时间码", labelEn: "Partial-range timecode", value: "按绝对源帧偏移重建", valueEn: "Regenerated at absolute source-frame offset" },
      { label: "48GB机器并发", labelEn: "48 GiB machine concurrency", value: "1个Archive-Exact原生worker", valueEn: "1 native Archive-Exact worker", note: "只改变调度，不改变随机种子或像素", noteEn: "Scheduling only; no seed or pixel change" },
      { label: "0-stop三段计算", labelEn: "Three 0-stop renders", value: "358.35秒总计 · 顺序执行", valueEn: "358.35s total · sequential" },
    ],
  },
];

v32.year = "上一版";
v32.status = "calibration";
versions.push({
  version: "V33",
  year: "当前基线",
  title: "不把现场绿光当错误：先锁定输入、曝光与黑场边界",
  status: "current",
  projection: { src: "/versions/v32-t031-projection.jpg", videoSrc: "/versions/v32-t031-projection-live-srgb.mp4", label: "T031 · V31正常5279 → 2383影院观察 · V33边界复验" },
  bluray: { src: "/versions/v32-t031-bluray.jpg", videoSrc: "/versions/v32-t031-bluray-live-srgb.mp4", label: "T031 · V31 5279 → Period 2K扫描 · V33黑场复验" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Panasonic官方V-709 · As Shot 0.00 stop见证" },
  summary: "V33不对轻微绿向做全局品红抵消，也不改变5279、颗粒、DIR、2383或扫描画面。它把FCP Standard参考、0 stop As Shot相机见证与+0.45 stop虚拟胶片EI明确分开；并在三段素材上为黑场裁切、toe占用、对比跨度、有效gamma、原生母版、部分区间音频/时间码和48GB机器内存安全建立可失败的交付门槛。Technical Neutral保留但关闭，直到灰卡/ColorChecker给出可重复证据。",
  changes: ["T002、T007、T031各增加24帧原生5.7K的0.00-stop As Shot V-709见证", "保留+0.45-stop虚拟胶片EI为显式参数，不再称作未处理相机默认", "FCP Standard T031源帧144成为SHA锁定的独立解码/显示见证", "硬黑、toe、p05–p95对比跨度、32级单调色调映射与有效log-luma power进入自动验收", "Technical Neutral接口保留但默认关闭；未获灰卡证据前不自动去绿", "部分区间音频改为采样精确PCM裁切，时间码按绝对源帧偏移重建", "48GB参考机器自动限制为单个Archive-Exact原生worker；质量与随机种子不变"],
  errors: ["第一次同时启动三段5.7K float基线造成不可接受的系统内存压力；panic报告显示压缩段已满并逼近swap耗尽，任务在重启时终止", "以三通道同时接近零定义黑场会漏掉有微小色差但亮度已到黑的像素；最终改用与FCP审计一致的Rec.709编码亮度阈值", "没有同光源中性卡时，无法把树林反射、as-shot白平衡与V-709局部残差唯一分离"],
  discoveries: ["中性数学输入经过BT.2020→V-Gamut→V-Log→官方V-709的最大通道扩散仅0.000589，拒绝全局矩阵绿偏", "扫描完成端的硬黑具有强场景依赖：T007几乎为零，而暗场T002/T031约为1–2%", "放映与扫描对相机基线的稳健色调映射在三场景中均保持单调，不存在隐藏的反转或gamma断点", "worker数量只影响调度；在48GB机器上限制并发比依赖大量swap更快也更可靠", "是否需要Technical Neutral现在是可由灰卡实验回答的问题，而不是靠观感决定的全局tint"],
  refs: ["R44", "R45", "R46", "R47", "R49"],
  parameters: v33Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002",
      note: "明亮天空、人物与暗部共同检验曝光标签、高光端、扫描黑位与综合色度。",
      projection: { src: "/versions/v31-t002-projection.jpg", videoSrc: "/versions/v31-t002-projection-live-srgb.mp4", label: "T002 · 正常5279 → 2383影院观察 · 图像冻结" },
      bluray: { src: "/versions/v31-t002-bluray.jpg", videoSrc: "/versions/v31-t002-bluray-live-srgb.mp4", label: "T002 · Period 2K扫描 · 图像冻结" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Panasonic V-709 · As Shot 0.00 stop" },
    },
    {
      name: "NJARAW_S001_S001_T007",
      note: "水面高光、细草和深色树林检验toe、亮度单调性与近零硬黑场景。",
      projection: { src: "/versions/v32-t007-projection.jpg", videoSrc: "/versions/v32-t007-projection-live-srgb.mp4", label: "T007 · 正常5279 → 2383影院观察 · 图像冻结" },
      bluray: { src: "/versions/v32-t007-bluray.jpg", videoSrc: "/versions/v32-t007-bluray-live-srgb.mp4", label: "T007 · Period 2K扫描 · 图像冻结" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Panasonic V-709 · As Shot 0.00 stop" },
    },
  ],
});

const v34Parameters: ParameterGroup[] = [
  {
    title: "5279处理后MTF边界", titleEn: "5279 PROCESSED-MTF BOUNDARY", items: [
      { label: "官方MTF条件", labelEn: "Official MTF condition", value: "钨丝灯曝光 · 推荐ECN-2处理后的5279", valueEn: "5279 tungsten-exposed and processed in recommended ECN-2" },
      { label: "显影邻接归属", labelEn: "Adjacency ownership", value: "只由处理后总MTF计算一次", valueEn: "Owned once by the processed-stock MTF" },
      { label: "V21重复项", labelEn: "V21 duplicate", value: "确定性层内DIR邻接归零", valueEn: "Deterministic intralayer DIR adjacency set to zero" },
      { label: "层间与颗粒", labelEn: "Interimage & grain", value: "冻结 · 不用公开资料无法识别的参数重调", valueEn: "Frozen · no retuning of publicly underidentified parameters" },
      { label: "48 μm RMS", labelEn: "48 μm RMS", value: "三记录曝光相关校准保留", valueEn: "Exposure-conditioned three-record calibration retained" },
    ],
  },
  {
    title: "单世代成片管线", titleEn: "SINGLE-GENERATION DELIVERY", items: [
      { label: "放映色彩边界", labelEn: "Projection colour boundary", value: "V31低频扫描a/b + 放映高频opponent + 放映Y", valueEn: "V31 scan low-frequency a/b + projection opponent detail + projection Y" },
      { label: "中间母版", labelEn: "Intermediate master", value: "取消", valueEn: "Removed" },
      { label: "ProRes世代", labelEn: "ProRes generations", value: "每个母版1次", valueEn: "One per master" },
      { label: "扫描隔离回归", labelEn: "Scan isolation regression", value: "管线探针与V30逐文件SHA-256一致", valueEn: "Pipeline probe file-SHA-256 identical to V30" },
      { label: "色彩空间", labelEn: "Colour space", value: "线性Rec.709内部适配 · 12-bit Rec.709 1-1-1交付", valueEn: "Linear Rec.709 adaptation · 12-bit Rec.709 1-1-1 delivery" },
    ],
  },
  {
    title: "速度、内存与发布门槛", titleEn: "SPEED, MEMORY & RELEASE GATES", items: [
      { label: "T020单帧", labelEn: "T020 single frame", value: "约36.08秒 · 两个母版", valueEn: "~36.08 s · both masters" },
      { label: "旧V30+V31", labelEn: "Old V30+V31", value: "约43.5秒/帧", valueEn: "~43.5 s/frame" },
      { label: "重复高斯", labelEn: "Dead Gaussian work", value: "9次原生全帧计算跳过 · 输出SHA不变", valueEn: "Nine native full-frame passes skipped · output SHA unchanged" },
      { label: "48 GiB并发", labelEn: "48 GiB concurrency", value: "1个原生worker", valueEn: "One native worker", note: "双worker虽更快但产生约6.6 GiB swap，已否决", noteEn: "Two workers were faster but produced ~6.6 GiB swap and were rejected" },
      { label: "三段压力测试", labelEn: "Three stress trials", value: "T002 0–23 · T007 276–299 · T031 132–155", valueEn: "T002 0–23 · T007 276–299 · T031 132–155" },
      { label: "一秒双母版实测", labelEn: "One-second dual-master timing", value: "T002 823.52秒 · T007 822.26秒 · T031 786.91秒", valueEn: "T002 823.52 s · T007 822.26 s · T031 786.91 s", note: "三段顺序总计2432.69秒；均含24帧、双观察器、音频/时间码与最终哈希", noteEn: "2432.69 s sequential total; each includes 24 frames, both observers, audio/timecode and final hashes" },
    ],
  },
];

const v33 = versions.find((item) => item.version === "V33");
if (v33) {
  v33.year = "上一版";
  v33.status = "calibration";
}
versions.push({
  version: "V34",
  year: "当前基线",
  title: "让显影邻接只发生一次，也让母版只编码一次",
  status: "current",
  projection: { src: "/versions/v34-t031-projection.jpg", videoSrc: "/versions/v34-t031-projection-live-srgb.mp4", label: "T031 · V34正常5279 → 2383影院观察 · 单世代" },
  bluray: { src: "/versions/v34-t031-bluray.jpg", videoSrc: "/versions/v34-t031-bluray-live-srgb.mp4", label: "T031 · V34 5279 → Period 2K扫描 · 单世代" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Panasonic官方V-709 · As Shot 0.00 stop见证" },
  summary: "V34来自一次完整的算法与渲染审计，而不是新的调色。Kodak 5279数据表的MTF是在钨丝灯曝光并经推荐ECN-2处理后测得；Kodak同时说明超过100%的MTF通常来自developer adjacency。旧管线先用V21确定性DIR增加一次邻接锐度，又应用已经拟合整条处理后MTF的核，形成约1–3.5%的局部重复。V34只移除这项重复，颗粒、层间DIR、三速度层、48 μm RMS、颜色、黑场与gamma均不凭观感重调；同时把V31颜色边界移到内存中，让放映和扫描各只经历一次ProRes编码。",
  changes: ["处理后5279 MTF成为确定性邻接锐度的唯一所有者", "V31颜色边界在两条完整观察器之后、交付编码之前执行", "取消V30中间母版的两次解码与放映二次编码", "Apple扩展线性BT.2020到胶片输入的空V-Gamut往返合并为同一矩阵乘积", "确定性系数归零后跳过9次无效原生高斯计算，输出SHA-256不变", "部分区间音频清单改为如实记录PCM裁切/无损重编码和时间码重建", "T002、T007、T031各以24帧原生5.7K 12-bit双母版验证"],
  errors: ["旧研究已经写明MTF是处理后整体响应，但V21加入确定性邻接后没有回头重拟合总MTF", "V31先编码V30两条母版，再解码做综合色边界并二次编码放映版；结果可重复但不是无损", "双worker在48 GiB机器上虽达到约28.85秒/帧，却产生约6.6 GiB swap，因此被质量与稳定性门槛否决", "旧的部分区间manifest把实际PCM无损重编码错误写成stream copied", "一个pre-V21 DIR函数已经没有调用却仍留在源码，给未来OFX移植制造歧义"],
  discoveries: ["官方处理后MTF与DIR化学不是两张可以直接相乘的独立清晰度贴图", "少一次ProRes世代既是提速，也是比更强并行更可靠的画质优化", "合并空的V-Gamut往返在原生帧上99.9926%的12-bit通道码相同，其余是单码舍入边界", "V34的扫描中位亮度与高光端基本不动；变化集中在被重复计算的局部边缘", "未来真正的大幅加速应来自驻留Metal/OpenFX图、资源复用和异步主机队列，而不是在48 GiB上堆Python进程"],
  refs: ["R1", "R21", "R46", "R54", "R55"],
  parameters: v34Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002",
      note: "天空、高光和暗部共同检验单世代成片不会改变黑白端点或制造综合色偏移。",
      projection: { src: "/versions/v34-t002-projection.jpg", videoSrc: "/versions/v34-t002-projection-live-srgb.mp4", label: "T002 · V34正常5279 → 2383影院观察" },
      bluray: { src: "/versions/v34-t002-bluray.jpg", videoSrc: "/versions/v34-t002-bluray-live-srgb.mp4", label: "T002 · V34 Period 2K扫描" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Panasonic V-709 · As Shot 0.00 stop" },
    },
    {
      name: "NJARAW_S001_S001_T007",
      note: "水面、细草与树林边缘检验重复邻接移除后的自然细节和时序颗粒。",
      projection: { src: "/versions/v34-t007-projection.jpg", videoSrc: "/versions/v34-t007-projection-live-srgb.mp4", label: "T007 · V34正常5279 → 2383影院观察" },
      bluray: { src: "/versions/v34-t007-bluray.jpg", videoSrc: "/versions/v34-t007-bluray-live-srgb.mp4", label: "T007 · V34 Period 2K扫描" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Panasonic V-709 · As Shot 0.00 stop" },
    },
  ],
});

const v35Parameters: ParameterGroup[] = [
  {
    title: "质量冻结与执行边界", titleEn: "QUALITY FREEZE & EXECUTION BOUNDARY", items: [
      { label: "图像模型", labelEn: "Image model", value: "V34完全冻结", valueEn: "V34 fully frozen" },
      { label: "不重调", labelEn: "No retune", value: "颜色 · 黑位 · gamma · MTF · DIR · 颗粒振幅/频谱", valueEn: "Colour · black · gamma · MTF · DIR · grain amplitude/spectrum" },
      { label: "Archive", labelEn: "Archive", value: "V34 NumPy/CPU · 字节级参考", valueEn: "V34 NumPy/CPU · byte-exact reference" },
      { label: "Production", labelEn: "Production", value: "独立但统计等价的随机实现", valueEn: "Independent, statistically equivalent realization" },
    ],
  },
  {
    title: "Philox-u32有限位点", titleEn: "PHILOX-U32 FINITE SITES", items: [
      { label: "生成器", labelEn: "Generator", value: "Philox4x32-10 · 全局像素坐标", valueEn: "Philox4x32-10 · global pixel coordinates" },
      { label: "伯努利阈值", labelEn: "Bernoulli threshold", value: "floor(float32 p × 2³²)", valueEn: "floor(float32 p × 2³²)" },
      { label: "实测p域", labelEn: "Observed p domain", value: "1.685×10⁻⁷ — 0.986325", valueEn: "1.685×10⁻⁷ — 0.986325" },
      { label: "实测n域", labelEn: "Observed n domain", value: "22个离散值 · 1—30", valueEn: "22 discrete values · 1—30" },
      { label: "概率量化误差", labelEn: "Probability error", value: "最大2.269×10⁻¹⁰", valueEn: "2.269×10⁻¹⁰ maximum" },
      { label: "身份审计", labelEn: "Identity audit", value: "45次/帧 · 重复0", valueEn: "45 calls/frame · 0 duplicates" },
    ],
  },
  {
    title: "速度、稳定性与验收", titleEn: "SPEED, STABILITY & GATES", items: [
      { label: "T002双母版", labelEn: "T002 dual masters", value: "26.200秒/帧 · 比V34快23.65%", valueEn: "26.200 s/frame · 23.65% faster than V34" },
      { label: "观察器", labelEn: "Observers", value: "可靠串行 · Numba workqueue并发被禁止", valueEn: "Reliable serial · unsafe Numba workqueue concurrency blocked" },
      { label: "颗粒能量偏差", labelEn: "Grain-energy departure", value: "放映≤0.1485% · 扫描≤0.2635%", valueEn: "Projection ≤0.1485% · scan ≤0.2635%" },
      { label: "时序差分能量", labelEn: "Temporal-difference energy", value: "放映≤0.1234% · 扫描≤0.1954%", valueEn: "Projection ≤0.1234% · scan ≤0.1954%" },
      { label: "交付", labelEn: "Delivery", value: "5760×4320 · 24帧 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 24 frames · 12-bit ProRes 4444 · Rec.709 1-1-1" },
    ],
  },
];

const v34 = versions.find((item) => item.version === "V34");
if (v34) {
  v34.year = "上一版";
  v34.status = "calibration";
}
versions.push({
  version: "V35",
  year: "当前基线",
  title: "不改变胶片，只改变计算：可审计的Production管线",
  status: "current",
  projection: { src: "/versions/v35-t031-projection.jpg", videoSrc: "/versions/v35-t031-projection-live-srgb.mp4", label: "T031 · V35正常5279 → 2383影院观察 · Philox-u32 Production" },
  bluray: { src: "/versions/v35-t031-bluray.jpg", videoSrc: "/versions/v35-t031-bluray-live-srgb.mp4", label: "T031 · V35 5279 → Period 2K扫描 · Philox-u32 Production" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Panasonic官方V-709 · As Shot 0.00 stop见证" },
  summary: "V35不是新调色，也不重写胶片。V34的颜色、黑位、gamma、MTF、DIR、颗粒振幅与频谱全部冻结；改变的是有限银盐位点的执行方式。每个像素、帧、记录层、速度层和尺寸类通过Philox4x32-10获得确定性身份，直接用完整uint32随机字与float32概率的2³²定点阈值执行伯努利试验。异步Metal采样与CPU期望密度滤波重叠，V31综合色边界复用内存。24帧、五区域的颜色、剪切、RGB高频相关、颗粒能量和时序差分验收全部通过，同时双母版比V34快23.65%。",
  changes: ["用Philox-u32直接伯努利试验替代24-bit逆CDF候选，实际概率量化误差降至2.269×10⁻¹⁰", "Metal有限位点异步提交并直接共享输出内存，与CPU期望密度滤波重叠", "每帧45个记录层/速度层/尺寸类身份被解码、去重并写入provenance", "所有结果记录素材、算法、Profile、LUT、桥接代码、命令与随机身份哈希", "V31综合色适配器复用全帧缓冲，V34摄影模型与所有艺术边界保持冻结", "T002、T007、T031各制作一秒原生5.7K 12-bit放映与扫描母版"],
  errors: ["最初把24-bit逆CDF称为exact-distribution过于绝对；统计通过不等于数学无限精度", "同进程并行观察器触发Numba workqueue SIGABRT，因此V35在解码前拒绝observer-workers=2", "共享内存子进程观察器虽逐字节相同，却因内存带宽竞争从10.94秒恶化到约25秒", "单Gaussian和全残差卷积虽然省0.65—0.9秒/帧，却让约5×10⁻⁶密度舍入被2383阈值放大为最高900—960个16-bit code的孤立差异，因此否决", "当前Python Metal桥仍有进程级设备/队列，只是研究工具，不能原样移植到OFX"],
  discoveries: ["质量优先不只意味着保留平均色彩；非线性印片链要求审计极端尾部和稀有阈值事件", "完整uint32 Bernoulli在30位点全幅微基准中反而比浮点逆CDF更快", "四个完整乳剂种子的层标准差比为0.999918/1.000264/0.999852，NPS差小于参考自身的种子波动", "24帧五区域比较没有系统性绿、蓝或品红偏移，扫描与放映的颗粒/时序能量偏差均低于0.3%", "OFX v1必须全帧、单实例串行、supportsTiles=false，并使用主机拥有的Metal队列与每实例资源环"],
  refs: ["R50", "R54", "R55", "R56", "R57"],
  parameters: v35Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002",
      note: "24帧完整验收场景：五区域颜色、剪切、RGB高频相关、颗粒能量与时序差分全部通过。",
      projection: { src: "/versions/v35-t002-projection.jpg", videoSrc: "/versions/v35-t002-projection-live-srgb.mp4", label: "T002 · V35正常5279 → 2383影院观察" },
      bluray: { src: "/versions/v35-t002-bluray.jpg", videoSrc: "/versions/v35-t002-bluray-live-srgb.mp4", label: "T002 · V35 Period 2K扫描" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Panasonic V-709 · As Shot 0.00 stop" },
    },
    {
      name: "NJARAW_S001_S001_T007",
      note: "水面、细草与树林检验高光、细纹理、低硬黑场景和有机时序颗粒。",
      projection: { src: "/versions/v35-t007-projection.jpg", videoSrc: "/versions/v35-t007-projection-live-srgb.mp4", label: "T007 · V35正常5279 → 2383影院观察" },
      bluray: { src: "/versions/v35-t007-bluray.jpg", videoSrc: "/versions/v35-t007-bluray-live-srgb.mp4", label: "T007 · V35 Period 2K扫描" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Panasonic V-709 · As Shot 0.00 stop" },
    },
  ],
});

const v36Parameters: ParameterGroup[] = [
  {
    title: "跨版本同帧契约", titleEn: "MATCHED-FRAME COMPARISON", items: [
      { label: "T002绝对帧", labelEn: "T002 absolute frames", value: "0–23", valueEn: "0–23" },
      { label: "T007绝对帧", labelEn: "T007 absolute frames", value: "276–299", valueEn: "276–299" },
      { label: "T031绝对帧", labelEn: "T031 absolute frames", value: "132–155", valueEn: "132–155" },
      { label: "比较门槛", labelEn: "Comparison gate", value: "相机/放映/扫描/静帧/视频必须同一窗口", valueEn: "Camera/projection/scan/still/video must share one window" },
      { label: "V35错误", labelEn: "V35 release error", value: "T007与T031误从第0帧开始", valueEn: "T007 and T031 incorrectly began at frame 0" },
    ],
  },
  {
    title: "35mm锐度与颗粒", titleEn: "35 MM SHARPNESS & GRANULARITY", items: [
      { label: "图像变化", labelEn: "Image change", value: "无 · V35胶片模型冻结", valueEn: "None · V35 film model frozen" },
      { label: "5279 MTF50", labelEn: "5279 MTF50", value: "R 51.12 · G 64.75 · B 72.26 cycles/mm", valueEn: "R 51.12 · G 64.75 · B 72.26 cycles/mm" },
      { label: "MTF峰值", labelEn: "MTF peaks", value: "R 102.23% · G 114.17% · B 121.36%", valueEn: "R 102.23% · G 114.17% · B 121.36%" },
      { label: "颗粒测量孔径", labelEn: "Granularity aperture", value: "48 μm · 原生映射11.10 px", valueEn: "48 μm · 11.10 px at native mapping" },
      { label: "物理解释", labelEn: "Physical interpretation", value: "密度构成图像；密度的空间传递构成锐度", valueEn: "Density forms the image; its spatial transfer forms sharpness" },
    ],
  },
  {
    title: "正确帧复验", titleEn: "CORRECT-FRAME REVALIDATION", items: [
      { label: "新采样器高频RMS", labelEn: "New sampler high-pass RMS", value: "V34比值1.00121", valueEn: "1.00121 vs V34" },
      { label: "时序差分RMS", labelEn: "Temporal-difference RMS", value: "V34比值1.00139", valueEn: "1.00139 vs V34" },
      { label: "颗粒/边缘比", labelEn: "Grain/base-edge ratio", value: "V34比值1.00131", valueEn: "1.00131 vs V34" },
      { label: "结论", labelEn: "Conclusion", value: "不缩小颗粒、不额外柔化", valueEn: "No grain reduction and no added softening" },
      { label: "母版", labelEn: "Masters", value: "5760×4320 · 24帧 · 12-bit ProRes 4444", valueEn: "5760×4320 · 24 frames · 12-bit ProRes 4444" },
    ],
  },
];

const v35 = versions.find((item) => item.version === "V35");
if (v35) {
  v35.year = "上一版";
  v35.status = "calibration";
  v35.errors.push("发布比较错误：T007与T031使用第0–23帧，而V34分别使用276–299与132–155；画面内容变化被误呈现为颗粒变化");
}
versions.push({
  version: "V36",
  year: "当前基线",
  title: "先比较同一帧，再判断35mm的颗粒与锐度",
  status: "current",
  projection: { src: "/versions/v36-t031-projection.jpg", videoSrc: "/versions/v36-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V36 5279 → 2383影院观察" },
  bluray: { src: "/versions/v36-t031-bluray.jpg", videoSrc: "/versions/v36-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V36 5279 → Period 2K扫描" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Frame 132–155 · Panasonic V-709 As Shot见证" },
  summary: "V36没有把颗粒磨细，也没有用额外柔化掩盖问题。审计发现V35的T007与T031都误从第0帧开始，而V34使用经过选择的第276帧与第132帧；不同画面运动和纹理因此被当成胶片版本差异。V36锁定相机、放映、扫描、静帧与悬停视频的绝对源帧，并重新核对5279处理后MTF与48 μm diffuse RMS颗粒：密度是画面变量，但只有密度的空间变化才是锐度。正确帧下V35 Production与V34的高频、时序和颗粒/边缘比只差约0.1%，因此胶片模型保持不动。",
  changes: ["锁定T002 0–23、T007 276–299、T031 132–155三个绝对源帧窗口", "网页每条分支明确显示源帧，禁止不同窗口伪装成版本对比", "在正确T031帧上拆分验证Philox采样器与Production空间核", "新增5279 MTF与48 μm granularity联合物理尺度审计", "保留V35颜色、黑位、gamma、MTF、DIR、颗粒振幅与频谱", "网页hover代理改用更短GOP与更高保真度，减少编码器把胶片颗粒变成块状沸腾"],
  errors: ["第一轮V36盐值筛选也错误使用第0帧，导致四组随机种子都出现相同假异常；发现帧契约后全部作废", "V35网站把三个场景都写成24帧验证，却没有把绝对起始帧作为发布失败条件", "单独比较MTF或48 μm RMS都不足以证明35mm观感；两者还必须共享画幅与观察尺度"],
  discoveries: ["V35 T031与新做的第0帧Production输出逐像素一致，证明异常来自片段选择而不是隐藏算法变化", "正确第132帧下Philox与V34的时序差分RMS中位比为1.00139，颗粒/边缘比为1.00131", "颗粒确实构成最终密度图像，但绝对密度不是锐度；MTF描述密度调制随空间频率的保留", "Kodak E-58明确指出噪声频率、负片与正片颗粒、两级MTF和放大倍率共同决定可见graininess", "质量优先也意味着拒绝为了修复错误对比而修改本来正确的胶片模型"],
  refs: ["R1", "R21", "R25", "R55", "R56"],
  parameters: v36Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002 · Frame 0–23",
      note: "V35与V34本来就使用同一窗口；V36保留它作为同帧控制组。",
      projection: { src: "/versions/v36-t002-projection.jpg", videoSrc: "/versions/v36-t002-projection-live-srgb.mp4", label: "T002 · Frame 0–23 · V36 2383影院观察" },
      bluray: { src: "/versions/v36-t002-bluray.jpg", videoSrc: "/versions/v36-t002-bluray-live-srgb.mp4", label: "T002 · Frame 0–23 · V36 Period 2K扫描" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Frame 0–23 · Panasonic V-709 As Shot" },
    },
    {
      name: "NJARAW_S001_S001_T007 · Frame 276–299",
      note: "恢复V34选择的水面、细草与树林窗口，以同一空间细节判断35mm颗粒和锐度。",
      projection: { src: "/versions/v36-t007-projection.jpg", videoSrc: "/versions/v36-t007-projection-live-srgb.mp4", label: "T007 · Frame 276–299 · V36 2383影院观察" },
      bluray: { src: "/versions/v36-t007-bluray.jpg", videoSrc: "/versions/v36-t007-bluray-live-srgb.mp4", label: "T007 · Frame 276–299 · V36 Period 2K扫描" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Frame 276–299 · Panasonic V-709 As Shot" },
    },
  ],
});

const v37Parameters: ParameterGroup[] = [
  {
    title: "乳剂时间结构", titleEn: "TEMPORAL EMULSION STRUCTURE", items: [
      { label: "位点更新", labelEn: "Site renewal", value: "每一帧独立 · 不平滑、不拖拽、不冻结", valueEn: "Independent every frame · no smoothing, advection or frozen plate" },
      { label: "积分相位", labelEn: "Integration phase", value: "稳定平衡 · 30°", valueEn: "Stable-balanced · 30°" },
      { label: "亚像素半径", labelEn: "Subpixel radius", value: "0.38原生像素 · 与V36相同", valueEn: "0.38 native pixel · unchanged from V36" },
      { label: "随机身份", labelEn: "Stochastic identity", value: "Philox4x32-10 · 每帧45个唯一身份", valueEn: "Philox4x32-10 · 45 unique identities/frame" },
      { label: "禁止项", labelEn: "Explicitly rejected", value: "时间相关颗粒、固定颗粒片、运动跟随噪点", valueEn: "Temporal correlation, fixed grain plates, motion-following noise" },
    ],
  },
  {
    title: "V37唯一改动", titleEn: "THE ONLY V37 IMAGE CHANGE", items: [
      { label: "颜色/H-D", labelEn: "Colour / H-D", value: "冻结V36", valueEn: "Frozen from V36" },
      { label: "黑位/gamma", labelEn: "Black / gamma", value: "冻结V36", valueEn: "Frozen from V36" },
      { label: "MTF/DIR", labelEn: "MTF / DIR", value: "冻结V36", valueEn: "Frozen from V36" },
      { label: "颗粒强度/尺寸", labelEn: "Grain amplitude / size", value: "冻结V36", valueEn: "Frozen from V36" },
      { label: "改变", labelEn: "Changed", value: "取消每帧全画面采样核旋转", valueEn: "Removed whole-frame sampling-kernel rotation" },
    ],
  },
  {
    title: "相位消融与交付", titleEn: "PHASE ABLATION & DELIVERY", items: [
      { label: "候选", labelEn: "Candidates", value: "0° / 30° / 90° · T031原生8帧", valueEn: "0° / 30° / 90° · 8 native T031 frames" },
      { label: "放映高频CV", labelEn: "Projection high-pass CV", value: "V36的0.400倍 · 约降60%", valueEn: "0.400× V36 · about 60% lower" },
      { label: "放映方向波动", labelEn: "Projection directional variation", value: "V36的0.287倍 · 约降71%", valueEn: "0.287× V36 · about 71% lower" },
      { label: "方向均值偏差", labelEn: "Mean directional shift", value: "放映+0.00596 · 扫描+0.00359", valueEn: "Projection +0.00596 · scan +0.00359" },
      { label: "母版", labelEn: "Masters", value: "5760×4320 · 24帧 · 12-bit ProRes 4444 · Rec.709 1-1-1", valueEn: "5760×4320 · 24 frames · 12-bit ProRes 4444 · Rec.709 1-1-1" },
    ],
  },
];

const v36Current = versions.find((item) => item.version === "V36");
if (v36Current) {
  v36Current.year = "上一版";
  v36Current.status = "calibration";
}
versions.push({
  version: "V37",
  year: "当前基线",
  title: "每一帧仍是新的胶片，但采样器不再整幅呼吸",
  status: "current",
  projection: { src: "/versions/v37-t031-projection.jpg", videoSrc: "/versions/v37-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V37稳定乳剂 → 2383影院观察" },
  bluray: { src: "/versions/v37-t031-bluray.jpg", videoSrc: "/versions/v37-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V37稳定乳剂 → Period 2K扫描" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Frame 132–155 · Panasonic V-709 As Shot见证" },
  summary: "V37回应本地QuickTime母版里像覆盖层一样的假沸腾。连续胶片帧本来就来自不同片段，银盐位点应逐帧独立；错误不在独立随机性，而在V36还让整幅画面的双线性亚像素采样相位每帧一起旋转，叠加了第二层数值动画。V37保留每帧全新的45组Philox乳剂身份，只把积分核改为30°稳定平衡相位。T031消融中，放映分支的全帧高频幅度波动约降60%，方向波动约降71%，同时保持平均方向中性。颜色、H-D、黑位、gamma、MTF、DIR、颗粒振幅、颗粒尺寸与两个观察器全部冻结。",
  changes: ["每帧继续生成独立银盐/染料云位点，不进行时间平滑、运动拖拽或颗粒片冻结", "移除每帧全画面亚像素相位旋转，改用30°稳定平衡积分相位", "对0°、30°、90°进行原生T031相位消融，拒绝0°固定方向偏好与90°过校正", "保持0.38像素亚像素半径、五尺寸类、三速度层和三色记录不变", "冻结V36全部颜色、密度、锐度、黑位、gamma和观察参数", "T002、T007、T031各制作一秒原生5.7K 12-bit放映与扫描母版"],
  errors: ["最初把V35 T031第0–23帧与V34第132–155帧比较，夸大了极端尾部差异；该结论已经正式作废", "固定0°虽显著稳定时间能量，却留下可测的水平/垂直偏好，因此不能直接发布", "只降低颗粒强度或把颗粒时间相关化会掩盖问题，同时违背逐格胶片乳剂独立性"],
  discoveries: ["独立随机场不等于整幅统计量必须每帧呼吸；数值积分核的全场变化会制造额外动画", "30°平衡相位在T031保留V36平均方向结构，同时把放映高频CV降至0.400倍", "扫描观察器的孔径和场景结构会掩盖部分相位收益，因此放映与扫描必须分开测量", "颗粒有机感来自逐帧独立的密度形成和稳定的成像算子共同作用，不来自让一张噪点贴图跟随画面", "连续颗粒中心与2383密度域印片仍值得未来研究，但没有通过同等门槛前不进入基线"],
  refs: ["R1", "R21", "R25", "R58", "R59"],
  parameters: v37Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002 · Frame 0–23",
      note: "固定墙面、暗部和细纹理控制场景；静帧与悬停视频来自同一24帧母版。",
      projection: { src: "/versions/v37-t002-projection.jpg", videoSrc: "/versions/v37-t002-projection-live-srgb.mp4", label: "T002 · Frame 0–23 · V37 2383影院观察" },
      bluray: { src: "/versions/v37-t002-bluray.jpg", videoSrc: "/versions/v37-t002-bluray-live-srgb.mp4", label: "T002 · Frame 0–23 · V37 Period 2K扫描" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Frame 0–23 · Panasonic V-709 As Shot" },
    },
    {
      name: "NJARAW_S001_S001_T007 · Frame 276–299",
      note: "水面、细草与树林验证细纹理没有被稳定相位磨平或冻结。",
      projection: { src: "/versions/v37-t007-projection.jpg", videoSrc: "/versions/v37-t007-projection-live-srgb.mp4", label: "T007 · Frame 276–299 · V37 2383影院观察" },
      bluray: { src: "/versions/v37-t007-bluray.jpg", videoSrc: "/versions/v37-t007-bluray-live-srgb.mp4", label: "T007 · Frame 276–299 · V37 Period 2K扫描" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Frame 276–299 · Panasonic V-709 As Shot" },
    },
  ],
});

const v37Current = versions.find((item) => item.version === "V37");
if (v37Current) {
  v37Current.year = "上一版";
  v37Current.status = "calibration";
  v37Current.errors.push("交付边界错误：已完成的显示线性观察结果再次使用摄影机BT.709 OETF编码，QuickTime与静帧因此呈现不同的暗部、对比和色浓度");
}

const v38Parameters: ParameterGroup[] = [
  {
    title: "唯一观察结果", titleEn: "ONE OBSERVER LIGHT", items: [
      { label: "胶片模型", labelEn: "Film model", value: "V37完全冻结", valueEn: "V37 frozen in full" },
      { label: "颜色/H-D/黑位", labelEn: "Colour / H-D / black", value: "无变化", valueEn: "No change" },
      { label: "颗粒/MTF/DIR", labelEn: "Grain / MTF / DIR", value: "无变化", valueEn: "No change" },
      { label: "改变位置", labelEn: "Changed boundary", value: "只在observer-linear之后", valueEn: "Only after observer-linear light" },
      { label: "显示线性一致性", labelEn: "Decoded-light agreement", value: "三场景平均通道误差0.009–0.062%", valueEn: "Three-scene mean channel error 0.009–0.062%" },
    ],
  },
  {
    title: "双交付", titleEn: "DUAL DELIVERY", items: [
      { label: "专业母版", labelEn: "Professional master", value: "Rec.709 · inverse BT.1886 γ2.4 · 1-1-1", valueEn: "Rec.709 · inverse BT.1886 γ2.4 · 1-1-1" },
      { label: "本机观看版", labelEn: "Mac viewing companion", value: "Rec.709原色 · sRGB传递 · MOV 1-13-1", valueEn: "Rec.709 primaries · sRGB transfer · MOV 1-13-1" },
      { label: "编码", labelEn: "Codec", value: "两者均为12-bit ProRes 4444", valueEn: "Both are 12-bit ProRes 4444" },
      { label: "网页", labelEn: "Web", value: "只从sRGB观看版生成", valueEn: "Derived only from the sRGB companion" },
      { label: "XDR参考模式", labelEn: "XDR reference mode", value: "HDTV Video (BT.709–BT.1886)", valueEn: "HDTV Video (BT.709–BT.1886)" },
    ],
  },
  {
    title: "一致性门槛", titleEn: "CONSISTENCY GATES", items: [
      { label: "源帧", labelEn: "Source frames", value: "T002 0–23 · T007 276–299 · T031 132–155", valueEn: "T002 0–23 · T007 276–299 · T031 132–155" },
      { label: "静帧", labelEn: "Still", value: "第12帧 · sRGB观看版直接解码", valueEn: "Frame 12 · direct sRGB-companion decode" },
      { label: "网页视频", labelEn: "Web video", value: "首帧=静帧 · sRGB · closed GOP 6", valueEn: "First frame=still · sRGB · closed GOP 6" },
      { label: "禁止", labelEn: "Rejected", value: "把P3/HDR当作额外饱和度或亮度", valueEn: "Using P3/HDR as extra saturation or brightness" },
      { label: "分辨率", labelEn: "Resolution", value: "5760×4320 · 24帧", valueEn: "5760×4320 · 24 frames" },
      { label: "实测总时间", labelEn: "Measured total time", value: "T002 666.67s · T007 670.00s · T031 659.50s", valueEn: "T002 666.67s · T007 670.00s · T031 659.50s" },
      { label: "每源帧", labelEn: "Per source frame", value: "27.48–27.92s · 同时生成四个12-bit视频", valueEn: "27.48–27.92s · four 12-bit videos generated together" },
    ],
  },
];

versions.push({
  version: "V38",
  year: "当前基线",
  title: "同一束观察光，只因显示目标不同而采用不同编码",
  status: "current",
  projection: { src: "/versions/v38-t031-projection.jpg", videoSrc: "/versions/v38-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V38 2383观察 · sRGB本机观看链" },
  bluray: { src: "/versions/v38-t031-bluray.jpg", videoSrc: "/versions/v38-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V38 Period 2K扫描 · sRGB本机观看链" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Frame 132–155 · Panasonic V-709 As Shot见证" },
  summary: "V38修正V37静帧自然、QuickTime视频却更黑更浓的问题。V37把已经完成2383或Period 2K观察的显示线性光再次送入摄影机BT.709 OETF；播放器和网页随后以不同传递方式解释同一组码值，暗部和色浓度因此分叉。V38冻结全部胶片成像，只让同一observer-linear结果分别进入inverse BT.1886专业母版与sRGB本机观看版。专业母版用于XDR的HDTV Video参考模式；QuickTime、JPEG和网页共享sRGB观看链。P3与HDR没有被用来制造额外颜色或亮度。",
  changes: ["冻结V37负片、2383、扫描、颜色、颗粒、MTF、DIR、黑位和gamma", "把交付输入明确为已经完成观察的display-linear Rec.709光，而不是scene-linear摄影机信号", "专业母版改为inverse BT.1886 gamma 2.4的12-bit Rec.709 ProRes 4444", "新增同样12-bit的sRGB QuickTime观看版，使当前Mac默认显示模式与JPEG一致", "JPEG与网页视频只从sRGB观看版的同一第12帧生成", "新增专业母版/本机观看版解码回同一线性光的一致性审计"],
  errors: ["V25以来的注释把摄影机OETF与BT.1886参考显示混为一条可逆链，但两者并非互逆", "原先网页验证只限制通道MAE≤2.5%与中位亮度差≤1%，足以让可见的暗部差异通过", "V37静帧是精确BT.709逆变换后转sRGB，视频则由QuickTime按Apple视频Gamma解释，因此两者从来没有真正共享ODT"],
  discoveries: ["在本项目中静帧更接近算法原本的observer-linear结果；视频的额外浓郁主要是交付和播放伪影", "Apple Silicon MacBook Pro的Liquid Retina XDR提供专门的BT.709–BT.1886参考模式，它比凭感觉扩到P3或HDR更适合本项目", "P3显示能力不会恢复已经在Rec.709观察器中压缩掉的颜色；强行扩色域只会更改坐标而不增加证据", "专业母版与sRGB观看版可以有不同码值，但解码回显示线性光后必须相同", "颜色、黑位和gamma的发布验证必须跨母版、静帧、网页视频与真实播放器，而不能只读文件标签"],
  refs: ["R26", "R27", "R29", "R60", "R61", "R62"],
  parameters: v38Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002 · Frame 0–23",
      note: "暗墙、toe与低色度纹理用于检查传递函数是否再次压黑。",
      projection: { src: "/versions/v38-t002-projection.jpg", videoSrc: "/versions/v38-t002-projection-live-srgb.mp4", label: "T002 · Frame 0–23 · V38 2383观察 · sRGB本机观看链" },
      bluray: { src: "/versions/v38-t002-bluray.jpg", videoSrc: "/versions/v38-t002-bluray-live-srgb.mp4", label: "T002 · Frame 0–23 · V38 Period 2K扫描 · sRGB本机观看链" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Frame 0–23 · Panasonic V-709 As Shot" },
    },
    {
      name: "NJARAW_S001_S001_T007 · Frame 276–299",
      note: "水面与绿色细节用于确认修正传递函数没有改变V37颗粒和颜色。",
      projection: { src: "/versions/v38-t007-projection.jpg", videoSrc: "/versions/v38-t007-projection-live-srgb.mp4", label: "T007 · Frame 276–299 · V38 2383观察 · sRGB本机观看链" },
      bluray: { src: "/versions/v38-t007-bluray.jpg", videoSrc: "/versions/v38-t007-bluray-live-srgb.mp4", label: "T007 · Frame 276–299 · V38 Period 2K扫描 · sRGB本机观看链" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Frame 276–299 · Panasonic V-709 As Shot" },
    },
  ],
});

const v38Delivery = versions.find((item) => item.version === "V38");
if (v38Delivery) {
  v38Delivery.year = "上一版";
  v38Delivery.status = "calibration";
}

const v39Parameters: ParameterGroup[] = [
  {
    title: "输入与冻结边界", titleEn: "INPUT & FROZEN BOUNDARY", items: [
      { label: "测试素材", labelEn: "Test sources", value: "T002 0–23 · T007 276–299 · T031 132–155", valueEn: "T002 0–23 · T007 276–299 · T031 132–155" },
      { label: "源格式", labelEn: "Source format", value: "GH7 / ProRes RAW HQ 12-bit · 5760×4320 · 24000/1001", valueEn: "GH7 / ProRes RAW HQ 12-bit · 5760×4320 · 24000/1001" },
      { label: "RAW观察", labelEn: "RAW observer", value: "Apple Standard ProRes RAW · extended-linear BT.2020 / D65", valueEn: "Apple Standard ProRes RAW · extended-linear BT.2020 / D65" },
      { label: "虚拟胶片EI", labelEn: "Virtual film EI", value: "+0.45 stop（不改相机As Shot见证）", valueEn: "+0.45 stop (camera As Shot witness unchanged)" },
      { label: "传感器噪声边界", labelEn: "Sensor-noise boundary", value: "photochemical · 不额外叠加数码噪点", valueEn: "photochemical · no added digital-noise layer" },
      { label: "35mm画幅宽度", labelEn: "35 mm image width", value: "24.9mm ↔ 5760px", valueEn: "24.9 mm ↔ 5760 px" },
      { label: "色彩/H-D/黑位/gamma", labelEn: "Colour / H-D / black / gamma", value: "冻结V38", valueEn: "Frozen from V38" },
      { label: "艺术调色", labelEn: "Creative grade", value: "无", valueEn: "None" },
    ],
  },
  {
    title: "5279密度形成", titleEn: "5279 DENSITY FORMATION", items: [
      { label: "图像变量", labelEn: "Image variable", value: "ECN-2后5279记录密度 D = −log₁₀T", valueEn: "Processed 5279 record density D = −log₁₀T" },
      { label: "MTF位置", labelEn: "MTF placement", value: "负片记录密度 · 在扫描/印片之前", valueEn: "Negative record density · before scan or printing" },
      { label: "颗粒形成", labelEn: "Grain formation", value: "3记录 × 3速度层 × 5粒径有限位点", valueEn: "3 records × 3 speed layers × 5 finite-site sizes" },
      { label: "48µm RMS约束", labelEn: "48 µm RMS constraint", value: "显影染料产额在随机DIR之前校准", valueEn: "Developed dye yield calibrated before stochastic DIR" },
      { label: "18%灰R/G/B门槛", labelEn: "18% gray R/G/B gate", value: "0.006135 / 0.008985 / 0.033836 D", valueEn: "0.006135 / 0.008985 / 0.033836 D" },
      { label: "官方目标R/G/B", labelEn: "Published targets R/G/B", value: "0.006144 / 0.008974 / 0.033930 D", valueEn: "0.006144 / 0.008974 / 0.033930 D" },
      { label: "时间结构", labelEn: "Temporal structure", value: "逐格新位点 · 30°稳定45类积分相位", valueEn: "Fresh sites each frame · stable 30° 45-class integration phase" },
    ],
  },
  {
    title: "冻结的35mm结构常数", titleEn: "FROZEN 35 MM STRUCTURE CONSTANTS", items: [
      { label: "快/中/慢速度偏移", labelEn: "Fast / mid / slow speed offsets", value: "0.0 / 0.5 / 1.3 logE", valueEn: "0.0 / 0.5 / 1.3 logE" },
      { label: "容量比例", labelEn: "Capacity fractions", value: "126 / 149 / 161（归一化）", valueEn: "126 / 149 / 161 (normalized)" },
      { label: "R记录ECD µm", labelEn: "R-record ECD µm", value: "1.28 / 0.83 / 0.58", valueEn: "1.28 / 0.83 / 0.58" },
      { label: "G记录ECD µm", labelEn: "G-record ECD µm", value: "1.36 / 0.79 / 0.52", valueEn: "1.36 / 0.79 / 0.52" },
      { label: "B记录ECD µm", labelEn: "B-record ECD µm", value: "1.14 / 0.88 / 0.68", valueEn: "1.14 / 0.88 / 0.68" },
      { label: "有效位点 R/G/B", labelEn: "Effective sites R/G/B", value: "17/60/79 · 16/64/88 · 22/55/70", valueEn: "17/60/79 · 16/64/88 · 22/55/70" },
      { label: "五级半径因子", labelEn: "Five radius factors", value: "0.62 / 0.78 / 0.98 / 1.22 / 1.55", valueEn: "0.62 / 0.78 / 0.98 / 1.22 / 1.55" },
      { label: "快层五级权重", labelEn: "Fast-layer weights", value: ".12 / .26 / .34 / .20 / .08", valueEn: ".12 / .26 / .34 / .20 / .08" },
      { label: "中层五级权重", labelEn: "Mid-layer weights", value: ".16 / .30 / .32 / .17 / .05", valueEn: ".16 / .30 / .32 / .17 / .05" },
      { label: "慢层五级权重", labelEn: "Slow-layer weights", value: ".22 / .34 / .29 / .12 / .03", valueEn: ".22 / .34 / .29 / .12 / .03" },
      { label: "5279 MTF core σ R/G/B", labelEn: "5279 MTF core σ R/G/B", value: ".85 / .67 / .60px @ 5760", valueEn: ".85 / .67 / .60 px @ 5760" },
      { label: "邻接量 R/G/B", labelEn: "Adjacency amount R/G/B", value: ".08 / .25 / .35 · 2px/6px带宽", valueEn: ".08 / .25 / .35 · 2 px / 6 px bands" },
      { label: "随机DIR", labelEn: "Stochastic DIR", value: "层间强度 .085 · 耦合尺度 .42", valueEn: "Interimage strength .085 · coupling scale .42" },
    ],
  },
  {
    title: "2383密度形成", titleEn: "2383 DENSITY FORMATION", items: [
      { label: "印片变量", labelEn: "Print variable", value: "2383 Status-A密度", valueEn: "2383 Status-A density" },
      { label: "2383 MTF位置", labelEn: "2383 MTF placement", value: "印片密度 · 在氙灯投影/监看之前", valueEn: "Print density · before xenon projection/monitor proof" },
      { label: "2383颗粒", labelEn: "2383 grain", value: "三个印片记录各自有限Poisson染料云", valueEn: "Independent finite Poisson dye clouds in each print record" },
      { label: "印片云半径/光学σ", labelEn: "Print cloud radius / optical σ", value: "0.42px / 0.28px @ 5760", valueEn: "0.42 px / 0.28 px @ 5760" },
      { label: "印片位点/密度尺度", labelEn: "Print sites / density scale", value: "520位点/原生像素面积 · 0.10×密度残差", valueEn: "520 sites/native-pixel area · 0.10× density residual" },
      { label: "显示叠加", labelEn: "Display overlay", value: "0 · 已删除亮度ratio颗粒", valueEn: "0 · luminance-ratio grain removed" },
      { label: "LAD R/G/B", labelEn: "LAD R/G/B", value: "1.09 / 1.06 / 1.03 D", valueEn: "1.09 / 1.06 / 1.03 D" },
      { label: "观察器", labelEn: "Observer", value: "空间2383密度后的完整分析观察器", valueEn: "Full analytical observer after spatial 2383 density" },
      { label: "193³输出缓存", labelEn: "193³ output cache", value: "V39正式画面不使用", valueEn: "Not used for the V39 image" },
    ],
  },
  {
    title: "RAW记录边界", titleEn: "RAW RECORD BOUNDARY", items: [
      { label: "旧顺序", labelEn: "Old order", value: "BT.2020→胶片RGB后先裁负值，再形成记录", valueEn: "Clip negative basis values before forming records" },
      { label: "V39顺序", labelEn: "V39 order", value: "保留有符号基底→记录灵敏度矩阵→物理曝光裁零", valueEn: "Preserve signed basis → record-sensitivity matrix → clamp physical exposure" },
      { label: "白平衡", labelEn: "White balance", value: "不改变 · 仍由Apple标准RAW转换/as-shot元数据拥有", valueEn: "Unchanged · still owned by Apple Standard RAW conversion/as-shot metadata" },
      { label: "受影响像素 T002/T007/T031", labelEn: "Affected pixels T002/T007/T031", value: "1.1113% / 0.2924% / 0.9971%", valueEn: "1.1113% / 0.2924% / 0.9971%" },
      { label: "用途", labelEn: "Purpose", value: "修复饱和色/深暗部的基底裁切，不做全局减绿", valueEn: "Correct saturated/deep-shadow basis clipping; no global green trim" },
    ],
  },
  {
    title: "交付、验证与效率", titleEn: "DELIVERY, VALIDATION & PERFORMANCE", items: [
      { label: "专业母版", labelEn: "Professional master", value: "5760×4320 · yuv444p12le ProRes 4444 · Rec.709 / BT.1886", valueEn: "5760×4320 · yuv444p12le ProRes 4444 · Rec.709 / BT.1886" },
      { label: "本机观看版", labelEn: "Mac viewing companion", value: "由实际母版反解 · 12-bit ProRes 4444 XQ · Rec.709原色 / sRGB传递", valueEn: "Derived from encoded master · 12-bit ProRes 4444 XQ · Rec.709 primaries / sRGB transfer" },
      { label: "参数所有权", labelEn: "Parameter ownership", value: "0.38px相位半径与0.72@2K综合色交叉由活动profile拥有", valueEn: "Active profile owns 0.38 px phase radius and 0.72@2K chroma crossover" },
      { label: "优化同一性", labelEn: "Optimization identity", value: "分析投影复用与双观察器共享：最大像素误差0.0", valueEn: "Analytical projection reuse and shared dual graph: max pixel error 0.0" },
      { label: "单帧探针", labelEn: "Single-frame probe", value: "63.26秒/源帧 · 同时生成四个12-bit视频", valueEn: "63.26s/source frame · four 12-bit videos together" },
      { label: "正式三场景计时", labelEn: "Formal three-scene timing", value: "T002 1372.71秒 · T007 1381.41秒 · T031 1497.69秒", valueEn: "T002 1372.71s · T007 1381.41s · T031 1497.69s", note: "72帧双观察器共4251.82秒；57.20–62.40秒/帧。XQ伴随版、音频/时间码与hash另137.15秒。", noteEn: "4251.82s for 72 dual-observer frames; 57.20–62.40s/frame. XQ companions, audio/timecode and hashes add 137.15s." },
      { label: "双交付线性光门槛", labelEn: "Dual-delivery light gate", value: "全部通过 · 最坏通道平均误差0.001092 < 0.0015", valueEn: "All passed · worst channel mean 0.001092 < 0.0015" },
    ],
  },
];

versions.push({
  version: "V39",
  year: "已撤回的实验",
  title: "颗粒不是正片上的残差：密度本身就是画面",
  status: "calibration",
  projection: { src: "/versions/v39-t031-projection.jpg", videoSrc: "/versions/v39-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V39 5279密度 → 2383密度 → 正常工艺监看" },
  bluray: { src: "/versions/v39-t031-bluray.jpg", videoSrc: "/versions/v39-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V39 5279密度 → Period 2K扫描" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Frame 132–155 · Panasonic V-709 As Shot见证" },
  summary: "V39解决完整代码与研究复查中发现的结构错位。V38虽然从有限银盐位点生成负片密度，但随后仍把MTF放到显示正片、把2383颗粒做成亮度ratio，并在随机DIR之后乘回48µm RMS；广色域到胶片记录也过早裁掉有符号基底。V39让5279 MTF作用于处理后负片密度，让公开RMS约束在随机DIR前决定显影染料产额，再让扫描器或2383观察这一份真实密度。2383自己的MTF与三记录染料云也在Status-A密度中形成，显示端不再加颗粒。颜色、H-D、黑位、gamma和双交付保持V38；这不是更好看的调色，而是把图像结构放回其测量域。",
  changes: ["将5279处理后MTF从display-linear RGB移入负片记录密度", "把5279 RMS约束移到随机DIR/层间耦合之前的显影染料产额", "将2383 MTF与三记录有限染料云移入Status-A印片密度", "删除最终显示亮度ratio式2383颗粒叠加", "BT.2020→胶片基底保留有符号分量，在记录曝光形成后只裁切一次", "修复0.38px相位半径和投影综合色交叉参数的profile所有权", "V38配置可在同一解释器中从V39完全复位", "准确分析观察器消除重复求值并共享双观察器中间量，优化前后逐像素相同", "sRGB观看版改从实际编码后的BT.1886母版反解，并用ProRes 4444 XQ保留V39高频密度结构"],
  errors: ["V38把公开的处理后负片MTF错误地作用于已经形成的正片显示RGB", "V38在随机DIR之后缩放组合残差，使化学耦合看不到正确幅度的显影事件", "V38的2383细颗粒是投影后亮度ratio，结构上仍像覆盖层", "V38在形成三条物理胶片记录之前裁掉广色域矩阵产生的负基底分量", "193³负片到最终输出缓存无法表达空间形成后的2383密度，因此V39正式画面改走完整分析观察器", "最初让BT.1886与sRGB从浮点光各自独立压缩；V39细密度结构暴露了两次有损ProRes实现不再完全一致"],
  discoveries: ["密度是图像变量，但密度数值本身不是锐度；MTF描述密度调制如何随空间频率传递", "MTF与颗粒必须处于同一物理几何和密度链中，但仍是两种独立可测量特性", "把RMS乘子移到化学之前可以修复层间作用次序，却不能凭公开曲线反推出Kodak未公开的涂层配方", "2383公开资料不足以识别曝光相关的三记录颗粒振幅，因此印片颗粒保持从属并明确标为证据边界", "V39的放映仍是正常工艺Rec.709监看证明，低频颜色边界包含时期扫描参照；纯物理投影函数保留但不冒充某一影院实测", "质量优先意味着V39不用快速点输出LUT近似空间2383；主要时间转移到准确观察器", "两个传递函数交付要共享实际母版的压缩结构；由母版派生的4444 XQ伴随版把最坏通道平均线性光误差压到0.001092"],
  refs: ["R1", "R4", "R5", "R7", "R25", "R44", "R45", "R47", "R58"],
  parameters: v39Parameters,
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T002 · Frame 0–23",
      note: "暗墙、toe与低色度纹理验证密度域颗粒、黑位和RAW记录裁切不会互相冒充。",
      projection: { src: "/versions/v39-t002-projection.jpg", videoSrc: "/versions/v39-t002-projection-live-srgb.mp4", label: "T002 · Frame 0–23 · V39 2383正常工艺监看" },
      bluray: { src: "/versions/v39-t002-bluray.jpg", videoSrc: "/versions/v39-t002-bluray-live-srgb.mp4", label: "T002 · Frame 0–23 · V39 Period 2K扫描" },
      camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Frame 0–23 · Panasonic V-709 As Shot" },
    },
    {
      name: "NJARAW_S001_S001_T007 · Frame 276–299",
      note: "水面、细草和高频绿色验证锐度传递与细颗粒属于同一35mm密度介质。",
      projection: { src: "/versions/v39-t007-projection.jpg", videoSrc: "/versions/v39-t007-projection-live-srgb.mp4", label: "T007 · Frame 276–299 · V39 2383正常工艺监看" },
      bluray: { src: "/versions/v39-t007-bluray.jpg", videoSrc: "/versions/v39-t007-bluray-live-srgb.mp4", label: "T007 · Frame 276–299 · V39 Period 2K扫描" },
      camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Frame 276–299 · Panasonic V-709 As Shot" },
    },
  ],
});

const v40Parameters: ParameterGroup[] = [
  {
    title: "发布边界", titleEn: "RELEASE BOUNDARY", items: [
      { label: "测试素材", labelEn: "Test sources", value: "T002 0–23 · T007 276–299 · T031 132–155", valueEn: "T002 0–23 · T007 276–299 · T031 132–155" },
      { label: "源与输出", labelEn: "Source and output", value: "GH7 ProRes RAW HQ 12-bit → 5760×4320 yuv444p12le", valueEn: "GH7 ProRes RAW HQ 12-bit → 5760×4320 yuv444p12le" },
      { label: "艺术调色", labelEn: "Creative grade", value: "无 · V38颜色、H-D、黑位、gamma冻结", valueEn: "None · V38 colour, H-D, black and gamma frozen" },
      { label: "V39状态", labelEn: "V39 status", value: "撤回 · 暗部跨记录彩色尖峰", valueEn: "Withdrawn · dark cross-record colour spikes" },
    ],
  },
  {
    title: "5279颗粒形成", titleEn: "5279 GRAIN FORMATION", items: [
      { label: "密度变量", labelEn: "Density variable", value: "处理后5279记录密度", valueEn: "Processed 5279 record density" },
      { label: "官方48µm RMS", labelEn: "Published 48 µm RMS", value: "回到处理后/层间耦合后的测量边界", valueEn: "Restored to the measured post-process/post-coupling boundary" },
      { label: "有限位点", labelEn: "Finite sites", value: "3记录 × 3速度层 × 5粒径 · V38/V37冻结", valueEn: "3 records × 3 speed layers × 5 sizes · frozen from V38/V37" },
      { label: "综合色积分", labelEn: "Opponent integration", value: "观察器内恢复；末端适配器不再重复加入高频综合色", valueEn: "Restored inside observers; the final adapter no longer re-adds high-frequency opponent colour" },
      { label: "显示叠加", labelEn: "Display overlay", value: "0", valueEn: "0" },
      { label: "Silver Efex旁证", labelEn: "Silver Efex evidence", value: "逆二项密度查表 + 实测片种形态；只进入独立FSD对照", valueEn: "Inverse-binomial density lookup + measured stock morphology; independent FSD control only" },
    ],
  },
  {
    title: "三管线受控对比", titleEn: "THREE-PIPELINE CONTROL", items: [
      { label: "物理5279", labelEn: "Physical 5279", value: "V40完整三记录乳剂、DIR、MTF与2383观察器", valueEn: "Full V40 three-record emulsion, DIR, MTF and 2383 observer" },
      { label: "FSD有限位点密度", labelEn: "FSD finite-site density", value: "N=176 · σ=0.597原生像素 · 512²逆二项查表", valueEn: "N=176 · σ=0.597 native px · 512² inverse-binomial lookup" },
      { label: "FSD混合", labelEn: "FSD mix", value: "观察器后sRGB信号亮度 · 固定综合色场 · 无独立RGB脉冲", valueEn: "Post-observer sRGB signal luma · fixed opponent field · no independent RGB impulses" },
      { label: "FSD色域边界", labelEn: "FSD gamut boundary", value: "只限制亮度位移，不随随机量缩放综合色", valueEn: "Limit density excursion only; never scale opponent colour with the variate" },
      { label: "确定性基线", labelEn: "Deterministic baseline", value: "同一5279均值、2383与颜色链；随机密度=0", valueEn: "Same 5279 mean, 2383 and colour chain; stochastic density=0" },
      { label: "比较边界", labelEn: "Comparison boundary", value: "FSD是独立对照，不替换V40物理模型", valueEn: "FSD is an independent control; it does not replace physical V40" },
    ],
  },
  {
    title: "2383与RAW证据边界", titleEn: "2383 & RAW EVIDENCE BOUNDARY", items: [
      { label: "2383确定性结构", labelEn: "Deterministic 2383 structure", value: "Status-A密度 + 官方MTF + 分析观察器", valueEn: "Status-A density + published MTF + analytical observer" },
      { label: "2383随机颗粒", labelEn: "Stochastic 2383 grain", value: "暂不声称 · 缺少分记录协方差/NPS", valueEn: "Withheld · no record covariance/NPS evidence" },
      { label: "V39有符号中间抵消", labelEn: "V39 signed intermediate cancellation", value: "撤回 · 胶片RGB先限制为非负再形成记录", valueEn: "Withdrawn · film RGB is bounded non-negative before record formation" },
      { label: "白平衡/RAW解码", labelEn: "White balance / RAW decode", value: "Apple Standard ProRes RAW边界不变", valueEn: "Apple Standard ProRes RAW boundary unchanged" },
      { label: "T003色卡见证", labelEn: "T003 chart witness", value: "Frame 160 · DGK DKC-Pro 5×7 · 18色块", valueEn: "Frame 160 · DGK DKC-Pro 5×7 · 18 patches" },
      { label: "源文件元数据", labelEn: "Source metadata", value: "GH7 · ISO 500 · 固定5500K · ProRes RAW HQ", valueEn: "GH7 · ISO 500 · fixed 5500 K · ProRes RAW HQ" },
      { label: "中性块2–4", labelEn: "Neutral patches 2–4", value: "平均R/G=1.175 · B/G=0.745 · 跨度1.91%/1.20%", valueEn: "Mean R/G=1.175 · B/G=0.745 · span 1.91%/1.20%" },
      { label: "灰阶可识别性", labelEn: "Gray-scale identifiability", value: "曝光尺度跨度0.318档 · 与色块位置/亮度混淆", valueEn: "Exposure-scale span 0.318 stops · confounded with patch position/lightness" },
      { label: "多帧复核", labelEn: "Multi-frame audit", value: "7帧 · 80–200 · 斜率1.137–1.147 · 灰阶跨度0.304–0.323档", valueEn: "7 frames · 80–200 · slope 1.137–1.147 · gray span 0.304–0.323 stops" },
      { label: "色卡网格修正", labelEn: "Chart-grid correction", value: "中排避开印刷文字带 · 撤回首轮综合色结论", valueEn: "Middle row excludes printed title strip · first chroma conclusion withdrawn" },
      { label: "合成D65灰轴", labelEn: "Synthetic D65 gray axis", value: "最大Δu′v′：扫描0.000174 · 放映0.000155", valueEn: "Maximum Δu′v′: scan 0.000174 · projection 0.000155" },
      { label: "恒定暖色阶梯", labelEn: "Constant warm ramp", value: "最大Δu′v′：扫描0.002530 · 放映0.002204", valueEn: "Maximum Δu′v′: scan 0.002530 · projection 0.002204" },
      { label: "暖色交叉状态", labelEn: "Warm crossover status", value: "模型中存在 · 5279幅度尚无匹配实测", valueEn: "Present in model · magnitude lacks a matched 5279 measurement" },
      { label: "黑位可识别性", labelEn: "Black-level identifiability", value: "6号块L*=23 · 不是零反射黑陷阱", valueEn: "Patch 6 is L*=23 · not a zero-reflectance black trap" },
      { label: "高光边界", labelEn: "Highlight boundary", value: "RAW白块三通道>1 · V-709仅1号白块1通道到顶", valueEn: "RAW white exceeds 1 in all channels · only V-709 patch 1 reaches one endpoint" },
      { label: "V40输入色域边界", labelEn: "V40 input-gamut boundary", value: "10号青块基底R=−0.01524 · 基底裁切使第一记录+19.29%", valueEn: "Cyan patch 10 basis R=−0.01524 · basis clip raises first record 19.29%" },
      { label: "色卡处理", labelEn: "Chart action", value: "不加全局品红/自动白平衡/新相机矩阵", valueEn: "No global magenta trim, auto white balance or new camera matrix" },
    ],
  },
  {
    title: "逐帧验收", titleEn: "EVERY-FRAME ACCEPTANCE", items: [
      { label: "彩色尖峰", labelEn: "Colour spikes", value: "144帧原生分辨率：综合色能量 + 3×3孤立原色脉冲", valueEn: "144 native frames: opponent energy + isolated 3×3 primary impulses" },
      { label: "审计有效域", labelEn: "Audit support", value: "中值半径1 + 邻域半径1；排除无效2px边界", valueEn: "Median radius 1 + neighbourhood radius 1; invalid 2 px perimeter excluded" },
      { label: "专业母版", labelEn: "Professional master", value: "12-bit Rec.709 / inverse BT.1886 ProRes 4444 XQ", valueEn: "12-bit Rec.709 / inverse BT.1886 ProRes 4444 XQ" },
      { label: "Mac观看版", labelEn: "Mac viewing copy", value: "从实际母版反解 · sRGB传递 · ProRes 4444 XQ", valueEn: "Decoded from actual master · sRGB transfer · ProRes 4444 XQ" },
      { label: "网站图像", labelEn: "Website imagery", value: "只从观看版第12帧派生；静帧/视频同帧验证", valueEn: "Derived only from viewing copy frame 12; still/motion identity gated" },
    ],
  },
];

versions.push({
  version: "V40",
  year: "当前基线",
  title: "准确的颗粒必须同时约束能量、协方差与极端尾部",
  status: "current",
  projection: { src: "/versions/v40-t031-projection.jpg", videoSrc: "/versions/v40-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V40 5279 → 2383正常工艺监看" },
  bluray: { src: "/versions/v40-t031-bluray.jpg", videoSrc: "/versions/v40-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V40 5279 → Period 2K扫描" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Frame 132–155 · Panasonic V-709 As Shot见证" },
  summary: "V40撤回V39中证据不足的三项推断：把Kodak处理后48µm RMS反推成DIR前源层目标、让边际记录RMS未经综合色积分直接进入观察结果，以及为2383虚构独立三记录Poisson颗粒。V40保留密度域5279/2383 MTF与已验证的颜色、黑位和gamma，把RMS约束放回公开文件真正测量的处理后边界，在扫描与放映观察器中恢复高频综合色积分，并阻止V31末端适配器把已经积分掉的综合色重新加回。没有2383协方差/NPS证据时停止生成其随机项。结果不是把彩噪模糊掉，而是拒绝制造未被证据识别的彩色自由度。",
  changes: ["将48µm颗粒度约束恢复到Kodak公开的处理后密度边界", "在扫描和2383观察器内恢复高频综合色积分", "关闭V31末端适配器重复加入的高频综合色残差", "撤回无分记录协方差/NPS证据的独立2383 Poisson颗粒", "撤回V39未识别的有符号胶片RGB中间抵消", "加入整体综合色能量与3×3孤立原色脉冲双重门槛", "第一代图像权威升级为12-bit ProRes 4444 XQ，并由其派生观看与网页图像", "加入FSD有限位点密度与无颗粒确定性基线，作为不改动V40物理模型的受控对照", "FSD改为观察器后sRGB信号密度形成并固定综合色场，撤回暗部色域边界随机缩放综合色的错误实现", "用T003 DKC-Pro色卡审计Apple标准RAW输入；证据显示现场暖向，因此不加入全局品红或自动白平衡"],
  errors: ["V39只对齐三条记录各自的RMS，却没有约束跨记录协方差和分布尾部", "Kodak数据表的48µm数值描述处理后胶片，不足以唯一反演DIR前各速度层的随机产额", "2383公开资料没有给出曝光相关三记录颗粒协方差或NPS，独立RGB Poisson是假精确", "V39的有符号中间胶片基底在暗绿色区域产生未识别的通道抵消", "V40恢复的硬基底裁切会改变落在Rec.709式中间基底之外的高饱和颜色；色卡证明该边界需要独立重测", "V31末端适配器曾在观察器之后再次加入高频综合色，抵消了V40第一次修正", "8-bit JPEG代表帧会平滑彩色脉冲，不能替代12-bit视频逐帧门禁"],
  discoveries: ["颗粒真实性不仅是RMS与大小；记录间协方差、偏度、极端尾部和观察器积分同样决定它像银盐还是数码彩噪", "密度仍然是图像变量，但公开的后验颗粒测量不能被任意移动到化学链更早的位置", "没有2383随机统计证据时，保留5279经印片MTF传递的结构比虚构印片颗粒更准确", "逐帧原生分辨率尾部审计比代表帧或缩小代理更能拦截稀疏彩色故障", "本机Silver Efex引擎确认核心是G=F⁻¹Binomial(N,p)(u)/N与Y′=(1−α)Y+αG，不是显示空间加噪", "Silver Efex每款黑白胶片拥有独立1000²实测形态；这只证明片种形态应独立建模，不能把黑白纹理冒充5279三记录参数", "FSD在线性RGB中形成亮度再经过sRGB编码会重新生成暗部色相脉冲；改在观察器后信号域形成密度并固定综合色场后，T002最强探针的两级孤立彩点均降为0", "FSD在不复制片种纹理的前提下，以N=176、σ=0.597px在T031校准帧匹配物理V40的亮度RMS、高频能量与空间相关；综合色残差保持更低，清楚暴露两条路线的物理边界", "DKC-Pro三排并非等高，中排上方有印刷文字带；首轮综合色采样因此被撤回，修正网格后跨组3×3在色相上中等泛化，相机输入矩阵仍是待受控光源验证的可能边界", "合成D65灰阶通过两观察器后最大Δu′v′低于0.00018，否证管线制造统一中性绿交叉；恒定暖色阶梯则出现0.00253/0.00220的曝光相关色彩交叉，其5279真实幅度仍待匹配实测", "10号高饱和青块证明V40的Rec.709式中间基底裁切会改变综合色：其第一记录曝光增加19.29%，扫描／放映Δu′v′约0.00226／0.00203；这不是RAW裁切，也不应与V39的随机故障混为一谈", "T003中性块2–5平均R/G=1.172、B/G=0.748，否证所有素材共享固定绿偏解码；真实日光条件仍不足以识别新白平衡、黑位或相机矩阵"],
  refs: ["R1", "R4", "R5", "R7", "R25", "R45", "R47", "R58", "R63", "R64", "R65", "R66"],
  parameters: v40Parameters,
  additionalTrials: [
    { name: "NJARAW_S001_S001_T002 · Frame 0–23", note: "暗墙、toe和低色度纹理用于最严格的暗部彩色尖峰审计。", projection: { src: "/versions/v40-t002-projection.jpg", videoSrc: "/versions/v40-t002-projection-live-srgb.mp4", label: "T002 · Frame 0–23 · V40 2383正常工艺监看" }, bluray: { src: "/versions/v40-t002-bluray.jpg", videoSrc: "/versions/v40-t002-bluray-live-srgb.mp4", label: "T002 · Frame 0–23 · V40 Period 2K扫描" }, camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Frame 0–23 · Panasonic V-709 As Shot" } },
    { name: "NJARAW_S001_S001_T007 · Frame 276–299", note: "水面、绿色细节和高频边缘用于综合色积分与35mm清晰度共存检查。", projection: { src: "/versions/v40-t007-projection.jpg", videoSrc: "/versions/v40-t007-projection-live-srgb.mp4", label: "T007 · Frame 276–299 · V40 2383正常工艺监看" }, bluray: { src: "/versions/v40-t007-bluray.jpg", videoSrc: "/versions/v40-t007-bluray-live-srgb.mp4", label: "T007 · Frame 276–299 · V40 Period 2K扫描" }, camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Frame 276–299 · Panasonic V-709 As Shot" } },
  ],
  pipelineComparisons: [
    {
      name: "T031 · Frame 132–155",
      note: "同一均值图、同一2383观察器，只改变密度形成机制。",
      noteEn: "Same mean image and 2383 observer; only the density-formation mechanism changes.",
      outputs: [
        { title: "V40物理5279", titleEn: "V40 PHYSICAL 5279", branch: { src: "/versions/v40-t031-projection.jpg", videoSrc: "/versions/v40-t031-projection-live-srgb.mp4", label: "完整三记录5279乳剂形成" } },
        { title: "FSD有限位点密度", titleEn: "FSD FINITE-SITE DENSITY", branch: { src: "/versions/v40-t031-fsd.jpg", videoSrc: "/versions/v40-t031-fsd-live-srgb.mp4", label: "逆二项密度形成的独立对照" } },
        { title: "无颗粒确定性基线", titleEn: "DETERMINISTIC NO-GRAIN", branch: { src: "/versions/v40-t031-deterministic.jpg", videoSrc: "/versions/v40-t031-deterministic-live-srgb.mp4", label: "随机密度关闭；颜色、MTF与观察器保持" } },
      ],
    },
    {
      name: "T002 · Frame 0–23",
      note: "暗部与低色度区域检验尾部、综合色与颗粒是否被误作显示噪声。",
      noteEn: "Shadows and low-chroma surfaces test tails, opponent colour and overlay-like noise.",
      outputs: [
        { title: "V40物理5279", titleEn: "V40 PHYSICAL 5279", branch: { src: "/versions/v40-t002-projection.jpg", videoSrc: "/versions/v40-t002-projection-live-srgb.mp4", label: "完整三记录5279乳剂形成" } },
        { title: "FSD有限位点密度", titleEn: "FSD FINITE-SITE DENSITY", branch: { src: "/versions/v40-t002-fsd.jpg", videoSrc: "/versions/v40-t002-fsd-live-srgb.mp4", label: "逆二项密度形成的独立对照" } },
        { title: "无颗粒确定性基线", titleEn: "DETERMINISTIC NO-GRAIN", branch: { src: "/versions/v40-t002-deterministic.jpg", videoSrc: "/versions/v40-t002-deterministic-live-srgb.mp4", label: "随机密度关闭；颜色、MTF与观察器保持" } },
      ],
    },
    {
      name: "T007 · Frame 276–299",
      note: "水面、高频边缘和绿色细节检验颗粒尺度与35mm锐度能否共存。",
      noteEn: "Water, fine edges and green detail test whether grain scale and 35 mm sharpness coexist.",
      outputs: [
        { title: "V40物理5279", titleEn: "V40 PHYSICAL 5279", branch: { src: "/versions/v40-t007-projection.jpg", videoSrc: "/versions/v40-t007-projection-live-srgb.mp4", label: "完整三记录5279乳剂形成" } },
        { title: "FSD有限位点密度", titleEn: "FSD FINITE-SITE DENSITY", branch: { src: "/versions/v40-t007-fsd.jpg", videoSrc: "/versions/v40-t007-fsd-live-srgb.mp4", label: "逆二项密度形成的独立对照" } },
        { title: "无颗粒确定性基线", titleEn: "DETERMINISTIC NO-GRAIN", branch: { src: "/versions/v40-t007-deterministic.jpg", videoSrc: "/versions/v40-t007-deterministic-live-srgb.mp4", label: "随机密度关闭；颜色、MTF与观察器保持" } },
      ],
    },
  ],
});

const v40 = versions[versions.length - 1];
v40.year = "上一基线";
v40.status = "calibration";

const v41Parameters: ParameterGroup[] = [
  {
    title: "色卡证据与校正边界", titleEn: "CHART EVIDENCE & CORRECTION BOUNDARY", items: [
      { label: "拟合见证", labelEn: "Fit witness", value: "T003 · Frame 160 · DKC-Pro 18色块", valueEn: "T003 · frame 160 · DKC-Pro 18 patches" },
      { label: "独立复核", labelEn: "Independent holdout", value: "T005 · Frame 160 · 更近、轻微失焦", valueEn: "T005 · frame 160 · closer, mildly defocused", note: "失焦不妨碍色块中位数；眩光较强的块不作为单独权威", noteEn: "Defocus does not invalidate patch medians; glare-heavy patches are not treated as standalone authority" },
      { label: "共同拍摄条件", labelEn: "Shared capture condition", value: "GH7 · ISO 500 · 5500 K · 户外方向光", valueEn: "GH7 · ISO 500 · 5500 K · directional outdoor light" },
      { label: "修正坐标", labelEn: "Correction basis", value: "D65线性BT.2020 → Bradford D50 XYZ色度偏差", valueEn: "D65 linear BT.2020 → Bradford D50 XYZ chroma deviation" },
      { label: "修正强度", labelEn: "Correction strength", value: "12.5% · 保守一步", valueEn: "12.5% · conservative step", note: "100%使植被与黄色明显过校正，25%仍令最终画面中位色度约+15%，均被否决", noteEn: "100% visibly over-corrected foliage/yellow; 25% still raised final median chroma about 15%; both were rejected" },
      { label: "明确禁止", labelEn: "Explicitly excluded", value: "自动白平衡、曝光、Gamma、黑位与艺术饱和度", valueEn: "Auto-WB, exposure, gamma, black and creative saturation" },
    ],
  },
  {
    title: "跨素材验证", titleEn: "CROSS-SOURCE VALIDATION", items: [
      { label: "T003合成色中位色相误差", labelEn: "T003 synthetic median hue error", value: "10.69° → 8.98°", valueEn: "10.69° → 8.98°" },
      { label: "T005合成色中位色相误差", labelEn: "T005 synthetic median hue error", value: "9.49° → 7.79°", valueEn: "9.49° → 7.79°" },
      { label: "T003自然色中位色相误差", labelEn: "T003 natural median hue error", value: "7.75° → 6.97°", valueEn: "7.75° → 6.97°" },
      { label: "T005自然色中位色相误差", labelEn: "T005 natural median hue error", value: "5.52° → 4.67°", valueEn: "5.52° → 4.67°" },
      { label: "输入亮度保持", labelEn: "Input luminance preservation", value: "两素材最大相对变化 < 1×10⁻⁵", valueEn: "Maximum relative change < 1×10⁻⁵ on both sources" },
      { label: "T005最终2383平均亮度", labelEn: "T005 final 2383 mean luminance", value: "相对V40 −0.43%", valueEn: "−0.43% versus V40" },
      { label: "T005最终2383中位色度", labelEn: "T005 final 2383 median chroma", value: "相对V40 +7.48%", valueEn: "+7.48% versus V40" },
    ],
  },
  {
    title: "记录边界", titleEn: "RECORD BOUNDARY", items: [
      { label: "V40边界", labelEn: "V40 boundary", value: "胶片中间基底先裁为非负", valueEn: "Clip the intermediate film basis non-negative" },
      { label: "V41边界", labelEn: "V41 boundary", value: "仅当三条5279记录曝光均非负时保留有符号中间值", valueEn: "Retain signed intermediates only when all three 5279 record exposures remain non-negative" },
      { label: "不安全回退", labelEn: "Unsafe fallback", value: "自动回到V40非负基底", valueEn: "Automatically return to V40's non-negative basis" },
      { label: "作用", labelEn: "Purpose", value: "避免高饱和青/绿的硬边界偏色，同时禁止V39式负曝光", valueEn: "Reduce hard-boundary hue error in saturated cyan/green while forbidding V39-style negative exposure" },
    ],
  },
  {
    title: "三管线与冻结参数", titleEn: "THREE PIPELINES & FROZEN PARAMETERS", items: [
      { label: "物理5279", labelEn: "Physical 5279", value: "V40颗粒、DIR、MTF、综合色积分全部冻结", valueEn: "V40 grain, DIR, MTF and opponent integration frozen" },
      { label: "FSD", labelEn: "FSD", value: "N=176 · σ=0.597px · 独立有限密度对照", valueEn: "N=176 · sigma 0.597 px · independent finite-density control" },
      { label: "确定性基线", labelEn: "Deterministic baseline", value: "同一颜色与观察器 · 随机密度=0", valueEn: "Same colour and observers · stochastic density=0" },
      { label: "黑位/对比/Gamma", labelEn: "Black / contrast / gamma", value: "与V40逐项冻结", valueEn: "Frozen item-for-item from V40" },
      { label: "交付", labelEn: "Delivery", value: "三素材各24帧 · 5760×4320 · 12-bit ProRes 4444 XQ", valueEn: "24 frames per source · 5760×4320 · 12-bit ProRes 4444 XQ" },
    ],
  },
  {
    title: "本机实测渲染时间", titleEn: "MEASURED RENDER TIME ON THIS MACHINE", items: [
      { label: "物理5279双母版", labelEn: "Physical 5279 dual masters", value: "52.72秒/帧 · 三素材平均", valueEn: "52.72 s/frame · three-source mean" },
      { label: "物理负片均值", labelEn: "Physical mean negative", value: "7.69秒/帧", valueEn: "7.69 s/frame" },
      { label: "随机乳剂", labelEn: "Stochastic emulsion", value: "6.38秒/帧", valueEn: "6.38 s/frame" },
      { label: "物理双观察器", labelEn: "Physical dual observer", value: "33.86秒/帧", valueEn: "33.86 s/frame", note: "当前最大的单项瓶颈", noteEn: "Current largest single-stage bottleneck" },
      { label: "FSD+确定性双分支", labelEn: "FSD + deterministic pair", value: "46.14秒/帧 · 三素材平均", valueEn: "46.14 s/frame · three-source mean" },
      { label: "FSD密度形成", labelEn: "FSD density formation", value: "2.65秒/帧", valueEn: "2.65 s/frame" },
      { label: "计时口径", labelEn: "Timing scope", value: "原生5760×4320 · 8线程 · 不含最终哈希", valueEn: "Native 5760×4320 · 8 threads · hashes excluded" },
    ],
  },
];

versions.push({
  version: "V41",
  year: "当前基线",
  title: "让色卡指出方向，但不让一次拍摄变成调色",
  status: "current",
  projection: { src: "/versions/v41-t031-projection.jpg", videoSrc: "/versions/v41-t031-projection-live-srgb.mp4", label: "T031 · Frame 132–155 · V41物理5279 → 2383正常工艺监看" },
  bluray: { src: "/versions/v41-t031-bluray.jpg", videoSrc: "/versions/v41-t031-bluray-live-srgb.mp4", label: "T031 · Frame 132–155 · V41物理5279 → Period 2K扫描" },
  fsd: { src: "/versions/v41-t031-fsd.jpg", videoSrc: "/versions/v41-t031-fsd-live-srgb.mp4", label: "T031 · Frame 132–155 · V41颜色 → FSD有限位点密度" },
  camera: { src: "/versions/v33-t031-camera-as-shot.jpg", videoSrc: "/versions/v33-t031-camera-as-shot-live-srgb.mp4", label: "T031 · Panasonic V-709 As Shot见证" },
  summary: "V41用T003色卡指出输入色度残差的方向，再用更近但轻微失焦的T005作为独立复核。两段素材在合成色与自然色上重复出同一类低饱和与色相残差，因此问题很可能存在；但二者都来自同一5500 K户外方向光，仍不足以建立完整GH7相机特性。V41只采用拟合矩阵的12.5%，保持线性亮度与中性轴，不碰白平衡、曝光、黑位、对比或Gamma。同时把V40的硬中间基底裁切改为“记录安全”的有符号传输：只有三条5279记录曝光全部非负时才保留，否则自动回退。",
  changes: ["加入T005近距离色卡作为未参与拟合的独立复核", "在Bradford D50色度偏差域建立跨组残差方向，并严格恢复D65场景亮度", "否决100%与25%过强修正，最终只采用12.5%保守步长", "T003与T005的合成色、自然色中位色相误差全部下降", "自然色色度误差在两个素材上同时改善", "用记录曝光非负作为有符号中间传输的物理安全条件", "V40颗粒、DIR、MTF、2383、扫描、黑位、对比与Gamma全部冻结", "物理5279、FSD与无颗粒确定性基线共享同一V41颜色入口"],
  errors: ["一次户外方向光色卡不能定量识别完整相机矩阵、光源SPD或5279专属综合色响应", "第一轮100%矩阵使植被与黄色明显过校正", "25%版本虽通过色卡，最终2383中位色度仍提升约15%，证据等级不足以支撑", "T005失焦不影响大色块中位数，但局部眩光和梯度限制单块精度", "V41仍是可回退的色度边界实验；均匀D65与钨丝灯色卡到来前不能称为最终GH7标定"],
  discoveries: ["失焦色卡仍可作为大面积色块统计见证，前提是采样远离边界并报告块内离散度", "独立素材重复同一方向，比在一张色卡上提高拟合阶数更有价值", "色卡空间的100%误差修正经过负片与2383非线性后会被放大，必须在最终成像结果再次设门槛", "保守12.5%步长在两个素材、两组色块上都降低色相误差，同时输入亮度变化低于1×10⁻⁵", "V40的非负中间基底不是RAW裁切；真正的物理条件是组合后的三条感光记录曝光不得为负", "FSD与物理5279应该共享颜色入口，但仍保持两种不同的密度形成假设"],
  refs: ["R1", "R4", "R26", "R27", "R44", "R47", "R58", "R63", "R66"],
  parameters: v41Parameters,
  additionalTrials: [
    { name: "NJARAW_S001_S001_T002 · Frame 0–23", note: "暗墙、toe与低色度纹理用于检查保守色度校正不会制造暗部彩点或改变黑位。", projection: { src: "/versions/v41-t002-projection.jpg", videoSrc: "/versions/v41-t002-projection-live-srgb.mp4", label: "T002 · V41物理5279 → 2383正常工艺监看" }, bluray: { src: "/versions/v41-t002-bluray.jpg", videoSrc: "/versions/v41-t002-bluray-live-srgb.mp4", label: "T002 · V41物理5279 → Period 2K扫描" }, fsd: { src: "/versions/v41-t002-fsd.jpg", videoSrc: "/versions/v41-t002-fsd-live-srgb.mp4", label: "T002 · V41颜色 → FSD有限位点密度" }, camera: { src: "/versions/v33-t002-camera-as-shot.jpg", videoSrc: "/versions/v33-t002-camera-as-shot-live-srgb.mp4", label: "T002 · Panasonic V-709 As Shot见证" } },
    { name: "NJARAW_S001_S001_T007 · Frame 276–299", note: "水面、高频边缘与绿色细节用于检查饱和度修正、35mm锐度和颗粒能否共存。", projection: { src: "/versions/v41-t007-projection.jpg", videoSrc: "/versions/v41-t007-projection-live-srgb.mp4", label: "T007 · V41物理5279 → 2383正常工艺监看" }, bluray: { src: "/versions/v41-t007-bluray.jpg", videoSrc: "/versions/v41-t007-bluray-live-srgb.mp4", label: "T007 · V41物理5279 → Period 2K扫描" }, fsd: { src: "/versions/v41-t007-fsd.jpg", videoSrc: "/versions/v41-t007-fsd-live-srgb.mp4", label: "T007 · V41颜色 → FSD有限位点密度" }, camera: { src: "/versions/v33-t007-camera-as-shot.jpg", videoSrc: "/versions/v33-t007-camera-as-shot-live-srgb.mp4", label: "T007 · Panasonic V-709 As Shot见证" } },
  ],
  pipelineComparisons: [
    ...(["t031", "t002", "t007"] as const).map((source) => ({
      name: source === "t031" ? "T031 · Frame 132–155" : source === "t002" ? "T002 · Frame 0–23" : "T007 · Frame 276–299",
      note: "同一V41颜色、5279均值与2383观察器；只改变随机密度形成机制。",
      noteEn: "Same V41 colour, 5279 mean and 2383 observer; only stochastic density formation changes.",
      outputs: [
        { title: "V41物理5279", titleEn: "V41 PHYSICAL 5279", branch: { src: `/versions/v41-${source}-projection.jpg`, videoSrc: `/versions/v41-${source}-projection-live-srgb.mp4`, label: "完整三记录5279乳剂形成" } },
        { title: "FSD有限位点密度", titleEn: "FSD FINITE-SITE DENSITY", branch: { src: `/versions/v41-${source}-fsd.jpg`, videoSrc: `/versions/v41-${source}-fsd-live-srgb.mp4`, label: "逆二项密度形成的独立对照" } },
        { title: "无颗粒确定性基线", titleEn: "DETERMINISTIC NO-GRAIN", branch: { src: `/versions/v41-${source}-deterministic.jpg`, videoSrc: `/versions/v41-${source}-deterministic-live-srgb.mp4`, label: "随机密度关闭；颜色、MTF与观察器保持" } },
      ],
    })),
  ],
});

const v41 = versions[versions.length - 1];
v41.year = "上一图像基线";
v41.status = "calibration";

const v42Parameters: ParameterGroup[] = [
  {
    title: "版本边界", titleEn: "VERSION BOUNDARY", items: [
      { label: "V42是什么", labelEn: "What V42 is", value: "研究一致性、执行图与交付权威版本", valueEn: "Research-conformance, execution-graph and delivery-authority release" },
      { label: "图像模型", labelEn: "Image model", value: "V41全部已接受成像参数冻结", valueEn: "All accepted V41 image-formation parameters frozen" },
      { label: "不声称", labelEn: "Not claimed", value: "新的5279光谱、涂层、DIR、NPS或相机标定", valueEn: "No new 5279 spectrum, coating, DIR, NPS or camera characterization" },
      { label: "当前画面见证", labelEn: "Current picture witness", value: "沿用V41同帧Production结果，等待V42完整一秒重渲染", valueEn: "V41 matched-frame Production witness retained pending the V42 one-second rerender" },
    ],
  },
  {
    title: "可执行研究门禁", titleEn: "EXECUTABLE RESEARCH GATES", items: [
      { label: "V37时间结构", labelEn: "V37 temporal structure", value: "逐帧独立位点 · 0.38px · 稳定30°积分", valueEn: "Independent frame sites · 0.38 px · stable 30° integration" },
      { label: "V40颗粒边界", labelEn: "V40 grain boundary", value: "处理后48µm RMS · 无虚构2383随机层 · 无重复综合色高频", valueEn: "Post-process 48 µm RMS · no invented 2383 population · no duplicate HF opponent path" },
      { label: "V41颜色边界", labelEn: "V41 colour boundary", value: "12.5%综合色残差 · D65亮度/中性轴保持 · 记录正值安全条件", valueEn: "12.5% chroma residual · D65 luminance/neutral preservation · record-positive safety" },
      { label: "失败行为", labelEn: "Failure behaviour", value: "任一常量漂移即拒绝baseline渲染", valueEn: "Any invariant drift refuses baseline rendering" },
    ],
  },
  {
    title: "Production与Archive", titleEn: "PRODUCTION & ARCHIVE", items: [
      { label: "默认Production", labelEn: "Production default", value: "Philox-u32 Bernoulli Metal · 每帧45身份唯一", valueEn: "Philox-u32 Bernoulli Metal · 45 unique identities per frame" },
      { label: "Archive参考", labelEn: "Archive reference", value: "CPU/NumPy保留，用于方程复现，不冒充同一颗粒实例", valueEn: "CPU/NumPy retained for equation reproduction, not the same grain realization" },
      { label: "冻结baseline控制", labelEn: "Frozen baseline controls", value: "+0.45 stop · grain 1.0 · oversample 1 · salt 0", valueEn: "+0.45 stop · grain 1.0 · oversample 1 · salt 0" },
      { label: "实验覆盖", labelEn: "Experimental overrides", value: "必须显式标记experimental，不能继续署名baseline", valueEn: "Must be explicitly labeled experimental and cannot retain baseline status" },
    ],
  },
  {
    title: "单一画面权威", titleEn: "SINGLE PICTURE AUTHORITY", items: [
      { label: "专业母版", labelEn: "Professional master", value: "5760×4320 · 12-bit ProRes 4444 XQ · Rec.709/BT.1886", valueEn: "5760×4320 · 12-bit ProRes 4444 XQ · Rec.709/BT.1886" },
      { label: "QuickTime伴随版", labelEn: "QuickTime companion", value: "解码实际母版 → 参考光 → sRGB → 12-bit XQ", valueEn: "Decode delivered master → reference light → sRGB → 12-bit XQ" },
      { label: "静帧", labelEn: "Still", value: "从母版派生sRGB路径的代表帧生成", valueEn: "Generated from the master-derived sRGB representative frame" },
      { label: "T003原生验证", labelEn: "Native T003 validation", value: "Frame 160 · 全部门禁通过 · 63.87秒 · 45/45身份 · 0重复", valueEn: "Frame 160 · all gates pass · 63.87 s · 45/45 identities · zero duplicates" },
      { label: "源流保留", labelEn: "Source streams", value: "24-bit PCM · 源帧偏移时间码12:32:56:08", valueEn: "24-bit PCM · source-frame-offset timecode 12:32:56:08" },
    ],
  },
  {
    title: "数据保护", titleEn: "DATA PROTECTION", items: [
      { label: "事故", labelEn: "Incident", value: "V41前引擎目录丢失 · 删除触发器未知", valueEn: "Pre-V42 engine directory lost · deletion trigger unknown" },
      { label: "恢复", labelEn: "Recovery", value: "895条编辑记录 → 199个文件", valueEn: "895 edit records → 199 files" },
      { label: "当前保护", labelEn: "Current protection", value: "218个作者文件 · Git远端 · SHA-256 manifest · CI", valueEn: "218 authored files · remote Git · SHA-256 manifest · CI", note: "V42恢复时为214；V43H新增4个受保护文件", noteEn: "214 at V42 recovery; V43H adds four protected files" },
      { label: "生成数据", labelEn: "Generated data", value: "视频不进Git；82MB缓存由版本化builder重建并核验hash", valueEn: "Video excluded; 82 MB cache rebuilt by versioned builder and hash-verified" },
    ],
  },
];

versions.push({
  version: "V42",
  year: "当前基线",
  title: "让研究结论成为引擎会主动守住的边界",
  status: "current",
  projection: { ...v41.projection, inherited: true, label: "T031 · V41同帧画面见证 · V42冻结图像模型 / 2383观察" },
  bluray: { ...v41.bluray, inherited: true, label: "T031 · V41同帧画面见证 · V42冻结图像模型 / Period 2K扫描" },
  fsd: v41.fsd ? { ...v41.fsd, inherited: true, label: "T031 · V41 FSD对照见证 · V42研究边界" } : undefined,
  camera: v41.camera ? { ...v41.camera, inherited: true } : undefined,
  summary: "V42不是一次新的调色，也不声称获得了新的5279测量。它冻结V41已接受的颜色、密度、颗粒、DIR、MTF、黑位、Gamma与双观察器，把V37–V41研究结论第一次写成引擎启动时必须通过的门禁。经验证的Philox-u32 Bernoulli Metal成为默认Production；Archive CPU保留为可复现参考，但不再把不同随机实现误称为同一颗粒。交付也只保留一份画面权威：先编码12-bit BT.1886母版，再从这个实际文件派生sRGB QuickTime与静帧。",
  changes: ["将新显式引擎正式命名为V42，避免软件“V2”与画面版本史混淆", "增加V37稳定相位、V40颗粒协方差修复、V41颜色/记录边界的运行时断言", "默认启用V35–V41验证过的Philox-u32 Bernoulli Metal Production图，并在发布前核验每帧45个随机身份完整且无重复", "保留Archive CPU与Reference NumPy作为研究参考，不要求逐颗粒复刻Production", "冻结baseline的+0.45 stop、grain 1.0、oversample 1与salt 0；任何修改必须标记实验", "只在成像阶段写BT.1886专业母版，sRGB和JPEG全部从编码后的实际母版派生；按V29契约恢复源音频与时间码", "修正旧恢复说明：字节一致证明的是Archive重构，不是Metal与NumPy产生同一颗随机乳剂", "公开记录V41实验引擎目录的数据丢失事故；将214个源代码、测试和研究文件纳入SHA-256清单与GitHub CI保护"],
  errors: ["V41以前的完整实验引擎只存在于本地、未纳入Git；原experiments/emulsion_reconstruction目录消失后必须从895条成功编辑记录恢复199个文件", "调查没有发现可归因给Claude、Python崩溃、macOS watchdog或某条清理命令的证据；删除触发原因保持unknown，不伪造结论", "V42当前公开主画面暂沿用V41同帧Production见证；正式V42一秒三素材重渲染尚未发布", "研究门禁能防止已知结论漂移，但不能替代尚不存在的5279 NPS、涂层和扫描器实测", "V41的12.5%色度残差仍是可回退的户外色卡证据，不因更名V42而升级为完整GH7特性"],
  discoveries: ["真正可确认的根因是关键源码只有一份未版本化副本；具体删除触发器无法由现存日志确定", "版本正确性不应由某一次随机颗粒的像素哈希定义，而应由成像方程、统计合同和交付权威共同定义", "Archive与Production可以产生不同乳剂实例，同时遵守同一H-D、48µm RMS、NPS和时间独立边界", "把研究常量做成运行时断言，可以阻止旧Profile泄漏或优化代码静默改写成像", "从实际12-bit母版派生全部观看文件，才能从结构上消除截图与视频成为两幅画面的可能"],
  refs: v41.refs,
  parameters: v42Parameters,
});

const v42 = versions[versions.length - 1];
v42.year = "研究基线";
v42.status = "calibration";

const v43hParameters: ParameterGroup[] = [
  {
    title: "版本边界", titleEn: "VERSION BOUNDARY", items: [
      { label: "版本类别", labelEn: "Release class", value: "假想版 · 预测，不是测量", valueEn: "Hypothesis Edition · prediction, not measurement" },
      { label: "问题", labelEn: "Question", value: "补全最可能但尚未测量的部分后，5279可能是什么样？", valueEn: "What might 5279 look like if the most likely unmeasured parts are completed?" },
      { label: "正式基线", labelEn: "Accepted baseline", value: "V42仍是研究一致性基线", valueEn: "V42 remains the research-conformant baseline" },
      { label: "没有加入", labelEn: "Not added", value: "白平衡、曝光、黑位、Gamma、饱和度或艺术调色", valueEn: "No white balance, exposure, black, gamma, saturation or creative grade" },
    ],
  },
  {
    title: "V43H新假设", titleEn: "V43H NEW HYPOTHESES", items: [
      { label: "负片相关尺度", labelEn: "Negative correlation scale", value: "V42 × 0.72", valueEn: "V42 × 0.72", note: "保持官方48µm RMS，只重新分配空间频谱", noteEn: "Official 48 µm RMS retained; only spatial spectrum is redistributed" },
      { label: "五级半径倍率", labelEn: "Five radius factors", value: "0.46 · 0.64 · 0.83 · 1.04 · 1.30", valueEn: "0.46 · 0.64 · 0.83 · 1.04 · 1.30" },
      { label: "五级光学倍率", labelEn: "Five optical factors", value: "0.72 · 0.83 · 0.94 · 1.06 · 1.18", valueEn: "0.72 · 0.83 · 0.94 · 1.06 · 1.18" },
      { label: "快层五级权重", labelEn: "Fast-layer weights", value: "0.10 · 0.25 · 0.36 · 0.22 · 0.07", valueEn: "0.10 · 0.25 · 0.36 · 0.22 · 0.07" },
      { label: "中层五级权重", labelEn: "Medium-layer weights", value: "0.17 · 0.32 · 0.32 · 0.15 · 0.04", valueEn: "0.17 · 0.32 · 0.32 · 0.15 · 0.04" },
      { label: "慢层五级权重", labelEn: "Slow-layer weights", value: "0.26 · 0.36 · 0.27 · 0.09 · 0.02", valueEn: "0.26 · 0.36 · 0.27 · 0.09 · 0.02" },
      { label: "Spirit候选权重", labelEn: "Spirit candidate weight", value: "25%", valueEn: "25%", note: "不是Spirit实测响应", noteEn: "Not a measured Spirit response" },
      { label: "Spirit中心 R/G/B", labelEn: "Spirit centres R/G/B", value: "622.5 · 542.5 · 467.5 nm", valueEn: "622.5 · 542.5 · 467.5 nm" },
      { label: "Spirit σ R/G/B", labelEn: "Spirit σ R/G/B", value: "49.4 · 41.8 · 36.1 nm", valueEn: "49.4 · 41.8 · 36.1 nm" },
      { label: "2383颗粒候选", labelEn: "2383 grain candidate", value: "光谱中性共模密度", valueEn: "spectrally neutral common density", note: "振幅取自三记录平均；禁止V39式独立RGB脉冲", noteEn: "Amplitude from the three-record mean; V39-style independent RGB impulses prohibited" },
      { label: "2383密度尺度 / 位点", labelEn: "2383 density scale / sites", value: "0.06 / 900", valueEn: "0.06 / 900" },
      { label: "2383半径 / 光学σ", labelEn: "2383 radius / optical σ", value: "0.30 / 0.23 px @ 5760", valueEn: "0.30 / 0.23 px @ 5760" },
    ],
  },
  {
    title: "三路模型与相机见证", titleEn: "THREE MODELS & CAMERA WITNESS", items: [
      { label: "放映", labelEn: "Projection", value: "同一V43H 5279负片 → 2383 → 氙灯观察", valueEn: "Same V43H 5279 negative → 2383 → xenon observer" },
      { label: "扫描", labelEn: "Scan", value: "同一V43H 5279负片 → Period Spirit / Cineon", valueEn: "Same V43H 5279 negative → period Spirit / Cineon" },
      { label: "FSD", labelEn: "FSD", value: "N=176 · σ=0.597px · 强度1.0", valueEn: "N=176 · σ=0.597 px · strength 1.0", note: "独立后观察器有限密度对照，不并入5279", noteEn: "Independent post-observer finite-density control; not merged into 5279" },
      { label: "相机原图", labelEn: "Camera witness", value: "Apple Standard ProRes RAW → Panasonic官方V-709 · 0 stop", valueEn: "Apple Standard ProRes RAW → Panasonic official V-709 · 0 stop" },
    ],
  },
  {
    title: "交付、门禁与效率", titleEn: "DELIVERY, GATES & PERFORMANCE", items: [
      { label: "专业母版", labelEn: "Professional master", value: "5760×4320 · 24帧 · 12-bit ProRes 4444 XQ · BT.1886", valueEn: "5760×4320 · 24 frames · 12-bit ProRes 4444 XQ · BT.1886" },
      { label: "QuickTime伴随版", labelEn: "QuickTime companion", value: "从实际母版解码 → sRGB · 12-bit XQ", valueEn: "Decoded from actual master → sRGB · 12-bit XQ" },
      { label: "随机身份", labelEn: "Stochastic identities", value: "45 / 帧 · 24帧1080次 · 0重复", valueEn: "45 / frame · 1,080 across 24 frames · zero duplicates" },
      { label: "V39彩噪门禁", labelEn: "V39 colour-spike gate", value: "逐帧暗部综合色尾部 + 孤立原色脉冲", valueEn: "Every-frame dark opponent tails + isolated primary impulses", note: "离散计数采用432项Bonferroni 1%全家族误报率", noteEn: "Discrete counts use a Bonferroni 1% family-wise false-rejection rate across 432 tests" },
      { label: "T020四路总耗时", labelEn: "T020 four-view wall time", value: "1708.30秒 · 28分28.30秒", valueEn: "1,708.30 s · 28m 28.30s" },
      { label: "T020有效每帧", labelEn: "T020 effective per frame", value: "71.18秒", valueEn: "71.18 s" },
      { label: "T020负片 / 双观察器 / FSD", labelEn: "T020 negative / dual observer / FSD", value: "13.89 / 49.00 / 3.08秒每帧", valueEn: "13.89 / 49.00 / 3.08 s per frame" },
      { label: "T032四路总耗时", labelEn: "T032 four-view wall time", value: "1725.66秒 · 71.90秒/帧", valueEn: "1,725.66 s · 71.90 s/frame" },
      { label: "T007四路总耗时", labelEn: "T007 four-view wall time", value: "1699.91秒 · 70.83秒/帧", valueEn: "1,699.91 s · 70.83 s/frame" },
    ],
  },
];

const v43hBranch = (source: string, branch: string, label: string): BranchImage => ({
  src: `/versions/v43h-${source}-${branch}.jpg`,
  videoSrc: `/versions/v43h-${source}-${branch}-live-srgb.mp4`,
  label,
});

versions.push({
  version: "V43H",
  year: "假想版",
  title: "把最可能、尚未测量的部分隔离成一场可撤回实验",
  status: "hypothesis",
  projection: v43hBranch("t020", "projection", "T020 · V43H 5279 → 2383氙灯放映"),
  bluray: v43hBranch("t020", "bluray", "T020 · V43H 5279 → Period 2K / Cineon扫描"),
  fsd: v43hBranch("t020", "fsd", "T020 · 独立FSD有限密度对照"),
  camera: v43hBranch("t020", "camera", "T020 · Panasonic官方V-709相机见证 · 无胶片管线"),
  summary: "V43H回答一个明确的假设问题：如果把现有研究中最可能、但仍没有直接测量的5279颗粒空间频谱、时期Spirit观察器与2383微弱颗粒补全，结果可能是什么样？V42的颜色、H-D、DIR、MTF、48µm RMS、黑位、Gamma与RAW解释全部冻结。V43H只在独立Profile内收窄35mm染料云频谱、向受资料约束的Spirit候选移动25%，并测试弱小、光谱中性的共模2383密度纹理。放映和扫描共享同一块实现的V43H负片；FSD保持独立；相机V-709只作原图见证。",
  changes: ["建立不污染V42的V43H独立Profile与hypothesis_not_measurement来源标签", "保留官方48µm RMS振幅，收窄和加密35mm颗粒的空间频谱", "Period扫描器只向受DFT架构与Kodak通用telecine曲线约束的候选移动25%", "加入弱小、由三记录平均估计振幅的2383光谱中性共模密度纹理，禁止独立RGB印片颗粒", "放映与扫描由同一次V43H负片显影共同产生，确定性观察器复用同一次光谱积分", "FSD继续作为独立有限密度路线，不升级成5279物理模型", "三个指定素材均输出放映、扫描、FSD和Panasonic官方V-709原图见证", "四路均先写原生5.7K 12-bit XQ母版，再从实际文件派生sRGB伴随版、静帧与网页hover视频"],
  errors: ["V43H的颗粒NPS不是Kodak测量；48µm RMS不能唯一决定空间频谱", "Spirit中心与带宽不是DFT公开响应，只是从宽观察器向合成候选的四分之一步", "2383三记录颗粒协方差和曝光相关NPS没有公开，因此共模项只能是从属预测", "T003/T005户外色卡不足以授权新白平衡、完整GH7矩阵或全局饱和度修正", "第一轮离散尖峰门禁错误地把Poisson期望计数当成硬上限；T007真实绿色边缘的17个候选只因超过ceil(14.7)=15而误判失败", "V43H通过交付门禁只证明内部一致，不能把预测参数变成5279事实"],
  discoveries: ["V39式坏电视彩噪的直接机制是未识别的2383独立RGB Poisson尾部；共模密度不会制造孤立原色尖峰", "同一观察器积分可以同时返回物理实现与确定性均值，FSD无需重新跑一遍193³光谱图", "T032同帧V42→V43H的平均通道变化小于0.001，保留了预测性差异而没有偷偷调色", "颗粒细腻程度可以在官方48µm RMS不变时改变，因为振幅积分与空间NPS不是同一约束", "随机事件率必须用统计上界审计：432项测试采用Bonferroni 1%全家族误报率，V39的上千/百万尖峰仍会数量级失败", "假想版最重要的产品边界不是好看，而是每一个未经测量的自由度都能被单独撤回"],
  refs: ["R1", "R4", "R7", "R8", "R21", "R25", "R44", "R49", "R58", "R59"],
  additionalTrials: [
    {
      name: "NJARAW_S001_S001_T032 · Frame 0–23",
      note: "雨天青绿、暗柱与低反差纹理：检查Spirit候选是否产生统一色偏，以及三路颗粒是否保持35mm尺度。",
      projection: v43hBranch("t032", "projection", "T032 · V43H 2383放映"),
      bluray: v43hBranch("t032", "bluray", "T032 · V43H Period 2K扫描"),
      fsd: v43hBranch("t032", "fsd", "T032 · FSD有限密度"),
      camera: v43hBranch("t032", "camera", "T032 · Panasonic官方V-709原图"),
    },
    {
      name: "NJARAW_S001_S001_T007 · Frame 276–299",
      note: "水面、绿色细节与较高局部饱和：检查颗粒/锐度匹配、综合色尾部和高频观察器积分。",
      projection: v43hBranch("t007", "projection", "T007 · V43H 2383放映"),
      bluray: v43hBranch("t007", "bluray", "T007 · V43H Period 2K扫描"),
      fsd: v43hBranch("t007", "fsd", "T007 · FSD有限密度"),
      camera: v43hBranch("t007", "camera", "T007 · Panasonic官方V-709原图"),
    },
  ],
  parameters: v43hParameters,
});

const v44Parameters: ParameterGroup[] = [
  {
    title: "证据边界", titleEn: "EVIDENCE BOUNDARY", items: [
      { label: "版本类别", labelEn: "Release class", value: "观察器与交付修订 · 不是新调色", valueEn: "Observer and delivery revision · not a new grade" },
      { label: "成像基线", labelEn: "Image-formation baseline", value: "回到V42已接受的5279负片模型", valueEn: "Accepted V42 5279 negative model" },
      { label: "撤回项", labelEn: "Withdrawn hypotheses", value: "V43H负片NPS、Spirit候选、2383随机颗粒", valueEn: "V43H negative NPS, Spirit candidate and stochastic 2383 grain" },
      { label: "保留约束", labelEn: "Retained constraints", value: "H-D · DIR · MTF · 48µm RMS · V41颜色边界", valueEn: "H-D · DIR · MTF · 48 µm RMS · V41 colour boundary" },
    ],
  },
  {
    title: "两种观察器", titleEn: "TWO OBSERVERS", items: [
      { label: "放映", labelEn: "Projection", value: "5279 → 2383亮度/纹理 → 48 nit监看", valueEn: "5279 → 2383 lightness/texture → 48 nit monitor" },
      { label: "扫描", labelEn: "Scan", value: "5279 → 已接受的时期2K / Cineon观察器", valueEn: "5279 → accepted period 2K / Cineon observer" },
      { label: "正常工艺颜色边界", labelEn: "Normal-process colour boundary", value: "保留V31 · 仅低频扫描参照色度", valueEn: "V31 retained · low-frequency scan-referenced chroma only", note: "直接解析放映颜色未通过暗部综合色门禁", noteEn: "Direct analytical projection colour failed the dark opponent-tail gate" },
      { label: "2383内生颗粒", labelEn: "Intrinsic 2383 grain", value: "0 · 等待实测NPS/协方差", valueEn: "0 · withheld pending measured NPS/covariance" },
    ],
  },
  {
    title: "尺度诚实的审看", titleEn: "SCALE-HONEST REVIEW", items: [
      { label: "专业母版", labelEn: "Professional master", value: "5760×4320 · 12-bit ProRes 4444 XQ · BT.1886", valueEn: "5760×4320 · 12-bit ProRes 4444 XQ · BT.1886" },
      { label: "审看版", labelEn: "Review file", value: "1920×1440 · 12-bit XQ · sRGB", valueEn: "1920×1440 · 12-bit XQ · sRGB" },
      { label: "采样顺序", labelEn: "Sampling order", value: "BT.1886反解 → 线性光面积积分 → sRGB", valueEn: "BT.1886 decode → linear-light area integration → sRGB" },
      { label: "锐利缩放伪高频", labelEn: "Sharp-resize false HF", value: "放映1.71× · 扫描1.21×", valueEn: "projection 1.71× · scan 1.21×", note: "相对面积积分审看的一帧T020测量", noteEn: "T020 one-frame measurement relative to area-integrated review" },
      { label: "静帧来源", labelEn: "Still authority", value: "最终编码视频的同一中间帧", valueEn: "Same middle frame decoded from final encoded movie" },
    ],
  },
];

const v44Branch = (branch: string, label: string): BranchImage => ({
  src: `/versions/v44-t020-${branch}.jpg`,
  videoSrc: `/versions/v44-t020-${branch}-live-srgb.mp4`,
  label,
});

versions.push({
  version: "V44",
  year: "观察器完整性",
  title: "让负片、观察器与显示尺度各自只承担自己的物理事实",
  status: "current",
  projection: v44Branch("projection", "T020 · V42负片模型 → 2383亮度/纹理 · 正常工艺监看颜色边界"),
  bluray: v44Branch("bluray", "T020 · V42负片模型 → Period 2K / Cineon扫描"),
  fsd: { ...v43hBranch("t020", "fsd", "T020 · 独立FSD有限密度对照 · 不并入V44"), inherited: true },
  camera: { ...v43hBranch("t020", "camera", "T020 · Panasonic官方V-709相机见证 · 无胶片管线"), inherited: true },
  summary: "V44不是另一组假想颗粒参数。它回应V43H在本机播放时出现的廉价粗粒感：撤回没有5279专属测量支持的NPS、Spirit与2383颗粒候选，回到V42已接受的负片模型；5.7K母版保持完整，同时新增从母版反解到线性观察光、按显示像素面积积分、再编码sRGB的审看版。一次失败实验也被正式记录：完全发布解析2383颜色会产生暗部高频彩色尾部，因此V44保留已验证的V31正常工艺颜色边界，不为了让两版更不一样而制造未经测量的投影颜色。网页静帧从最终视频同一帧反解。",
  changes: ["撤回V43H三个未测量候选，恢复V42负片形态和已接受的时期扫描器", "保留已验证的V31正常工艺监看边界：2383亮度/纹理加低频扫描参照染料色度", "没有2383三记录NPS/协方差前，2383随机颗粒保持为零", "保留5760×4320 12-bit XQ母版，不以模糊母版解决播放器缩放问题", "新增BT.1886反解、线性光像素面积积分、sRGB编码的1920审看链", "静帧改为从最终编码视频的同一帧生成，消除编码前后双重画面权威", "把电影胶片拷贝、telecine/蓝光转移与网页显示明确分成三个证据边界"],
  errors: ["V43H用官方48µm RMS约束一个猜测NPS，但一个孔径积分不能唯一识别空间频谱", "V43H加入了没有公开三记录统计支持的2383共模颗粒；消融证明它只解释约0.33%的高频能量", "第一份V44候选完全关闭V31颜色边界；24帧门禁发现放映暗部综合色p99.99为0.04882，且每百万暗像素约127个>0.06的孤立脉冲，因此整版拒绝发布", "5.7K随机结构若由播放器采用锐利缩放，会把超出显示Nyquist的能量折回成粗糙假纹理", "V44仍不是5279实拍/同批2383/已知扫描器的测量闭环，不能声称绝对复刻"],
  discoveries: ["用户看到的粗颗粒主要不是Wavefront加速误差，也不是新增2383颗粒，而是成像结构与播放器缩放共同作用", "同一帧中Lanczos审看相对线性光面积积分把放映高频抬到1.71倍、扫描抬到1.21倍", "正确的解决方案是保持原生母版并提供尺度明确的审看派生，不是任意模糊胶片模型", "真正的胶片放映、telecine/蓝光扫描和现代参考截图拥有不同光源、白点、分辨率与完成决策，不能互相充当颜色真值", "当前证据只能支持scan-referenced正常工艺投影监看；两版颜色相近是已声明的限制，比猜测一个更戏剧化的投影颜色准确", "投影机闪烁、显影条纹等可见特征应留作未来可测模块，不能因为它们听起来像胶片就加入客观baseline"],
  refs: ["R1", "R4", "R7", "R8", "R25", "R27", "R29", "R60", "R67"],
  parameters: v44Parameters,
});

for (const version of versions) {
  for (const branch of [version.projection, version.bluray]) {
    branch.src = withBasePath(branch.src);
    if (branch.videoSrc) branch.videoSrc = withBasePath(branch.videoSrc);
  }
  if (version.camera) {
    version.camera.src = withBasePath(version.camera.src);
    if (version.camera.videoSrc) version.camera.videoSrc = withBasePath(version.camera.videoSrc);
  }
  if (version.fsd) {
    version.fsd.src = withBasePath(version.fsd.src);
    if (version.fsd.videoSrc) version.fsd.videoSrc = withBasePath(version.fsd.videoSrc);
  }
  for (const trial of version.additionalTrials ?? []) {
    for (const branch of [trial.projection, trial.bluray]) {
      branch.src = withBasePath(branch.src);
      if (branch.videoSrc) branch.videoSrc = withBasePath(branch.videoSrc);
    }
    if (trial.camera) {
      trial.camera.src = withBasePath(trial.camera.src);
      if (trial.camera.videoSrc) trial.camera.videoSrc = withBasePath(trial.camera.videoSrc);
    }
    if (trial.fsd) {
      trial.fsd.src = withBasePath(trial.fsd.src);
      if (trial.fsd.videoSrc) trial.fsd.videoSrc = withBasePath(trial.fsd.videoSrc);
    }
  }
  for (const comparison of version.pipelineComparisons ?? []) {
    for (const output of comparison.outputs) {
      output.branch.src = withBasePath(output.branch.src);
      if (output.branch.videoSrc) output.branch.videoSrc = withBasePath(output.branch.videoSrc);
    }
  }
}

export const references = [
  { id: "R1", title: "KODAK VISION 500T 5279 / 7279 Technical Data, H-1-5279t", type: "Kodak片种数据", url: "https://125px.com/docs/motionpicture/kodak/5279.pdf" },
  { id: "R2", title: "Exploring the Color Image", type: "Kodak技术读物", url: "https://www.kodak.com/content/products-brochures/Film/Exploring-the-Color-Image.pdf" },
  { id: "R3", title: "Processing KODAK Motion Picture Films, Module 7: ECN-2", type: "Kodak处理规范", url: "https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-7.pdf" },
  { id: "R4", title: "KODAK VISION Color Print Film 2383 / 3383 Technical Data", type: "Kodak正片数据", url: "https://www.kodak.com/content/products-brochures/Film/VISION-Color-Print-Film-2383-3383-TECHNICAL-DATA.pdf" },
  { id: "R5", title: "LAD — Laboratory Aim Density, KODAK H-61", type: "Kodak实验室控制", url: "https://www.kodak.com/content/products-brochures/Film/LAD-Laboratory-Aim-Density.pdf" },
  { id: "R6", title: "US 5,298,376 — DIR inhibitor transport and colour saturation", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US5298376A/en" },
  { id: "R7", title: "US 5,314,793 — multilayer speed and granularity architecture", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US5314793A/en" },
  { id: "R8", title: "Spirit DataCine / Spirit HD technical data", type: "DFT扫描器资料", url: "https://www.dft-film.com/downloads/datasheets/DFT-Spirit-HD-datasheet-11-09.pdf" },
  { id: "R9", title: "Digital Intermediates, August 2003", type: "同期后期制作报道", url: "https://www.postmagazine.com/Publications/Post-Magazine/2003/August-1-2003/DIGITAL-INTERMEDIATES.aspx" },
  { id: "R10", title: "Charlie’s Angels: Full Throttle — technical specifications", type: "完成态参考", url: "https://www.imdb.com/title/tt0305357/technical/" },
  { id: "R11", title: "US 5,500,316 — colour negative contrast adjusted for electronic scanning", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US5500316A/en" },
  { id: "R12", title: "US 5,705,327 — nonlinear curve shape for telecine transfer", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US5705327A/en" },
  { id: "R13", title: "The Chemistry of Kodak Film — Smarter Every Day 275-C", type: "柯达工厂访谈", url: "https://www.youtube.com/watch?v=zJ8aNPStQ8M" },
  { id: "R14", title: "Kodak’s Film Quality Control Process — 275-B", type: "柯达工厂质控", url: "https://www.youtube.com/watch?v=VIH0dEMyv9w" },
  { id: "R15", title: "Advanced Emulsion: crystals, couplers, masks and processing", type: "Kodak资料支持的讲解", url: "https://www.youtube.com/watch?v=I4_7tW-cx1I" },
  { id: "R16", title: "Digital Color Management for Motion Picture Film", type: "IS&T / Ado Ishii, 2003", url: "https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/cic/11/1/art00055" },
  { id: "R17", title: "US 2002/0118211 — analytical dye density and interimage measurement", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US20020118211A1/en" },
  { id: "R18", title: "US 8,654,192 — LAD-anchored print-exposure matrix", type: "Adobe Systems专利", url: "https://patents.google.com/patent/US8654192B2/en" },
  { id: "R19", title: "Common LUT Format implementation guide", type: "ACES规范", url: "https://docs.acescentral.com/clf/guides/" },
  { id: "R20", title: "ISO 5-3:2009 — Photography and graphic technology: Spectral conditions", type: "ISO标准索引", url: "https://www.iso.org/standard/52915.html" },
  { id: "R21", title: "The Essential Reference Guide for Filmmakers", type: "Kodak电影胶片参考指南", url: "https://www.kodak.com/content/products-brochures/Film/kodak-essential-reference-guide-for-filmmakers.pdf" },
  { id: "R22", title: "Noise Power Spectra of Photographic Dye Images", type: "IS&T影像结构研究（反转片，仅作形态先验）", url: "https://library.imaging.org/admin/apis/public/api/ist/website/downloadArticle/print4fab/22/1/art00038_2" },
  { id: "R23", title: "US 4,536,472 — dye-cloud diffusion, Wiener spectrum and low-frequency mottle", type: "Eastman Kodak专利", url: "https://patents.google.com/patent/US4536472A/en" },
  { id: "R24", title: "EP 0,905,561 — speed-layer coupler coverage and spectrally differentiated dye records", type: "Eastman Kodak扫描型负片专利（非5279配方）", url: "https://patents.google.com/patent/EP0905561A1/en" },
  { id: "R25", title: "Print Grain Index — An Assessment of Print Graininess from Color Negative Films, E-58", type: "Kodak技术资料（2000年7月）", url: "https://125px.com/docs/techpubs/kodak/e58-2000_07.pdf" },
  { id: "R26", title: "ITU-R BT.709 — HDTV production and programme exchange", type: "ITU视频色度与信号标准", url: "https://www.itu.int/rec/R-REC-BT.709" },
  { id: "R27", title: "ITU-R BT.1886 — HDTV studio display EOTF", type: "ITU SDR参考显示标准", url: "https://www.itu.int/rec/R-REC-BT.1886" },
  { id: "R28", title: "Digital Cinema System Specification", type: "DCI数字影院规范", url: "https://www.dcimovies.com/dci-specification/" },
  { id: "R29", title: "CSS Color Module Level 4 — sRGB and web colour", type: "W3C网页颜色标准", url: "https://www.w3.org/TR/css-color-4/" },
  { id: "R30", title: "ACES 2 Output Transform parameters and display encodings", type: "Academy色彩管理规范", url: "https://docs.acescentral.com/system-components/output-transforms/parameters/" },
  { id: "R31", title: "ITU-R BT.1886-0 — Reference electro-optical transfer function", type: "ITU官方公式与黑白端点定义", url: "https://www.itu.int/dms_pubrec/itu-r/rec/bt/r-rec-bt.1886-0-201103-i%21%21pdf-e.pdf" },
  { id: "R32", title: "DCI Compliance Test Plan — calibrated screen luminance 48 cd/m²", type: "DCI影院白场测试条件", url: "https://ctp.dcimovies.com/0b5699a0b76a57547576565b89fd052467c8ac20/ctp.html" },
  { id: "R33", title: "US 6,815,153 — improved speed and granularity in high-speed colour negative film", type: "Eastman Kodak专利（分层机制，不是5279配方）", url: "https://patents.google.com/patent/US6815153B2/en" },
  { id: "R34", title: "US 6,190,847 — Kodak DIR diffusion-factor assay", type: "Eastman Kodak专利（测量机制，不是5279常数）", url: "https://patents.google.com/patent/US6190847B1/en" },
  { id: "R35", title: "EP 1,016,902 — green-only ECN-2 exposure as an interimage exclusion control", type: "Eastman Kodak专利（实验逻辑）", url: "https://data.epo.org/publication-server/rest/v1.2/publication-dates/20000705/patents/EP1016902NWA2/document.pdf" },
  { id: "R36", title: "Process ECN-2, H-24 processing modules", type: "Kodak处理与控制文件", url: "https://www.kodak.com/en/motion/page/processing-manuals/" },
  { id: "R37", title: "ISO 5-3 density spectral conditions and aperture dependence", type: "摄影密度测量标准", url: "https://www.iso.org/standard/52915.html" },
  { id: "R38", title: "US 7,899,113 — film-grain simulation identifiers and model database", type: "Thomson专利（5279条目无公开参数）", url: "https://patents.google.com/patent/US7899113B2/en" },
  { id: "R39", title: "JVT-H022 — SEI message for film grain encoding", type: "ITU JVT一手技术提案", url: "https://www.itu.int/wftp3/av-arch/jvt-site/2003_05_Geneva/JVT-H022.zip" },
  { id: "R40", title: "JVT-I013r2 — film grain encoding syntax and results", type: "ITU JVT一手技术提案", url: "https://www.itu.int/wftp3/av-arch/jvt-site/2003_09_SanDiego/JVT-I013r2.zip" },
  { id: "R41", title: "US provisional 60/462,389 — A Method for Simulating Film Grain on Encoded Video Sequences", type: "2003年原始临时专利（5279编号沿革，无数值参数）", url: "https://register.epo.org/application?documentId=EICL6DDCDHELFI4&number=EP04714129&lng=en&npl=false" },
  { id: "R42", title: "IPR2024-00572 Patent Owner Response — public JVT reflector exhibit index", type: "USPTO PTAB一手诉讼记录（公开邮件证据止于2002年）", url: "https://ptacts.uspto.gov/ptacts/public-informations/petitions/1555393/download-documents?artifactId=A34-fZL5CXNXG62kNfWGg1GSA8OwEYSpw1lTl1gtjcJR3Ahd7rnGyY0" },
  { id: "R43", title: "USPTO Patent Assignment reel 041214 / frame 0001 — Thomson to Dolby", type: "USPTO官方权利转让记录（专利继受不等于研究档案保管）", url: "https://assignmentcenter.uspto.gov/ipas/search/api/v2/public/download/patent/41214/1" },
  { id: "R44", title: "Panasonic Apple ProRes RAW Output LUT — RAW Gamut to V-Log/V-Gamut", type: "Panasonic官方Camera LUT说明（含GH7兼容列表）", url: "https://av.jpn.support.panasonic.com/support/global/cs/dsc/download/lut/s1h_raw_lut/index.html" },
  { id: "R45", title: "Apply built-in camera LUTs in Final Cut Pro", type: "Apple官方RAW转换与Camera LUT阶段说明", url: "https://support.apple.com/en-am/guide/final-cut-pro/ver5d55de8fd/mac" },
  { id: "R46", title: "Adjust camera settings in Final Cut Pro", type: "Apple官方ProRes RAW线性与Log工作流说明", url: "https://support.apple.com/en-euro/guide/final-cut-pro/ver3eb60032c/mac" },
  { id: "R47", title: "CVProResRawMetadata", type: "Apple Core Video开发者文档", url: "https://developer.apple.com/documentation/corevideo/cvproresrawmetadata" },
  { id: "R48", title: "LAD for KODAK VISION Color Print Film — H-61B", type: "Kodak官方2383通道目标密度", url: "https://www.kodak.com/content/products-brochures/Film/LAD-for-KODAK-VISION-Color-Print-Film-H-61b.pdf" },
  { id: "R49", title: "Panasonic V-Log to V-709 3D LUT", type: "Panasonic官方显示转换（含GH7）", url: "https://av.jpn.support.panasonic.com/support/global/cs/dsc/download/lut/index.html" },
  { id: "R50", title: "Numba Threading Layers — extra notes", type: "Numba官方并发安全文档", url: "https://numba.readthedocs.io/en/stable/user/threading-layer.html" },
  { id: "R51", title: "Process ECP-2D Specifications, H-24 Module 9A", type: "Kodak正常正片漂白／定影规范", url: "https://www.kodak.com/content/products-brochures/Film/Processing-KODAK-Motion-Picture-Films-Module-9A.pdf" },
  { id: "R52", title: "Motion Picture Film Processing Information — skip bleach / ENR", type: "Kodak特殊工艺说明", url: "https://www.kodak.com/en/motion/page/processing-information/" },
  { id: "R53", title: "SMPTE ST 428-1:2019 — D-Cinema Distribution Master image characteristics", type: "SMPTE数字影院母版标准", url: "https://pub.smpte.org/pub/st428-1/st428-1-2019.pdf" },
  { id: "R54", title: "OpenFX Image Effect Plug-in Rendering", type: "OpenFX官方渲染与Metal主机队列规范", url: "https://openfx.readthedocs.io/en/main/Reference/ofxRendering.html" },
  { id: "R55", title: "Metal Performance Shaders tuning hints", type: "Apple官方GPU调优指南", url: "https://developer.apple.com/documentation/metalperformanceshaders/tuning-hints" },
  { id: "R56", title: "Parallel Random Numbers: As Easy as 1, 2, 3 — Random123 / Philox", type: "SC11同行评审论文", url: "https://www.thesalmons.org/john/random123/papers/random123sc11.pdf" },
  { id: "R57", title: "Metal Best Practices — Command Buffers", type: "Apple官方命令缓冲与同步指南", url: "https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/CommandBuffers.html" },
  { id: "R58", title: "Realistic Film Grain Rendering", type: "IPOL同行评审论文与可复现实作（Newson et al., 2017）", url: "https://www.ipol.im/pub/art/2017/192/" },
  { id: "R59", title: "A Reproduction Model of Film Grain Texture for Digital Movies", type: "电影颗粒Wiener频谱研究（Munekata et al., 2011）", url: "https://www.researchgate.net/publication/314091949_A_Reproduction_Model_of_Film_Grain_Texture_for_Digital_Movies" },
  { id: "R60", title: "Evaluating video using QuickTime test pattern files", type: "Apple官方QuickTime Gamma与ColorSync测试说明", url: "https://developer.apple.com/documentation/avfoundation/evaluating-video-using-quicktime-test-pattern-files" },
  { id: "R61", title: "Use presets and reference modes with your Apple display", type: "Apple官方BT.709–BT.1886与P3参考模式说明", url: "https://support.apple.com/en-ca/108321" },
  { id: "R62", title: "MacBook Pro (16-inch, 2024) Technical Specifications", type: "Apple官方Liquid Retina XDR与P3规格", url: "https://support.apple.com/en-us/121554" },
  { id: "R63", title: "Nik Silver Efex User Guide — Film Grain (Branded)", type: "DxO官方产品技术说明", url: "https://userguides.dxo.com/nikcollection/en/silver-efex/" },
  { id: "R64", title: "Nik Color Efex User Guide — Grain engine and calibrated branded films", type: "DxO官方颗粒引擎说明", url: "https://userguides.dxo.com/nikcollection/en/color-efex/" },
  { id: "R65", title: "DxO — The science of film: calibrated grain matrices by tone region", type: "DxO官方胶片测量方法", url: "https://www.dxo.com/en/technology/science-of-film" },
  { id: "R66", title: "Complete Guide to Using the DKC-Pro Color Chart — colourimetry data", type: "DGK Color Tools官方色卡说明与CIELAB参考值", url: "https://dgkcolor.tools/wp-content/uploads/2019/09/Complete-Guide-to-the-DKC-Pro-Color-Chart_Final.pdf" },
  { id: "R67", title: "How Hollywood Fakes the 90s Film Look Today — Walter Volpatto interview", type: "调色师实践证词（观察器边界，不是5279测量）", url: "https://www.youtube.com/watch?v=rSKAV2AQ4I4" },
];

export const refMap = Object.fromEntries(references.map((ref) => [ref.id, ref]));
