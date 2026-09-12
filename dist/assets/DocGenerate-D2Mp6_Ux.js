import{_ as J,o as n,c as d,a as t,b as o,w as a,F as T,l as z,g,I as K,f as p,t as b,J as A,K as B,L as Q,r as i,m as k,M as W,d as G,e as q,N as R,O as Y,P as Z,Q as ee,x as le,H as P}from"./index-B0RETnkV.js";const te={class:"doc-page"},oe={class:"container doc-section"},ae={key:0,class:"type-grid"},se=["onClick"],ne={class:"type-card__icon"},re={class:"type-card__name"},ce={class:"type-card__desc"},ie={key:1,class:"form-card"},de={class:"form-card__title"},pe={class:"form-actions"},ue={key:2,class:"result-card"},_e={key:0,class:"generating"},me={class:"generating__text"},fe={class:"result-head"},ve={class:"result-title"},ge={class:"doc-preview"},be={class:"result-actions"},he={__name:"DocGenerate",setup(ye){const S=[{key:"loan",name:"借款合同",desc:"适用于个人/企业间资金借贷",icon:R,fields:[{prop:"lender",label:"出借人（甲方）",placeholder:"请输入出借人姓名或单位名称"},{prop:"borrower",label:"借款人（乙方）",placeholder:"请输入借款人姓名或单位名称"},{prop:"amount",label:"借款金额（元）",placeholder:"如：50000"},{prop:"period",label:"借款期限",placeholder:"如：自2026年1月1日至2027年1月1日"},{prop:"rate",label:"约定年利率（%）",placeholder:"如：4（留空则视为无息）"}]},{key:"labor",name:"劳动合同",desc:"用人单位与劳动者签订用工合同",icon:Y,fields:[{prop:"employer",label:"用人单位（甲方）",placeholder:"请输入单位全称"},{prop:"worker",label:"劳动者（乙方）",placeholder:"请输入劳动者姓名"},{prop:"position",label:"工作岗位",placeholder:"如：前端开发工程师"},{prop:"period",label:"合同期限",placeholder:"如：固定期限三年"},{prop:"salary",label:"月工资（元）",placeholder:"如：12000"}]},{key:"rent",name:"租赁合同",desc:"房屋、设备等租赁事项约定",icon:Z,fields:[{prop:"lessor",label:"出租方（甲方）",placeholder:"请输入出租方姓名或单位名称"},{prop:"lessee",label:"承租方（乙方）",placeholder:"请输入承租方姓名或单位名称"},{prop:"target",label:"租赁物及地址",placeholder:"如：某市某区某小区1栋201室"},{prop:"rent",label:"月租金（元）",placeholder:"如：3500"},{prop:"period",label:"租赁期限",placeholder:"如：2026年3月1日至2027年3月1日"}]},{key:"complaint",name:"民事起诉状",desc:"向法院提起民事诉讼的标准文书",icon:ee,fields:[{prop:"plaintiff",label:"原告信息",placeholder:"姓名、性别、身份证号、住址、联系方式"},{prop:"defendant",label:"被告信息",placeholder:"姓名/单位名称、住址、联系方式"},{prop:"claim",label:"诉讼请求",placeholder:"如：1.判令被告偿还借款5万元；2.本案诉讼费由被告承担"},{prop:"reason",label:"事实与理由",placeholder:"请简要描述纠纷经过"}]}],u=k(0),_=k(null),m=le({}),D=k(!1),f=k(0),$=k("");let w=null;const N=W(()=>{var l;return((l=_.value)==null?void 0:l.fields)??[]}),X=l=>{_.value=l,Object.keys(m).forEach(e=>delete m[e]),u.value=1},V=()=>{u.value=0},E=()=>{const l=N.value.find(e=>{var r;return!((r=m[e.prop])!=null&&r.trim())});if(l){P.warning(`请填写「${l.label}」`);return}u.value=2,F()},F=()=>{D.value=!0,f.value=0,$.value="",clearInterval(w),w=setInterval(()=>{f.value+=Math.floor(Math.random()*12)+6,f.value>=100&&(f.value=100,clearInterval(w),$.value=L(),D.value=!1)},120)},L=()=>{const l=m,e=new Date().toLocaleDateString("zh-CN",{year:"numeric",month:"long",day:"numeric"});switch(_.value.key){case"loan":return`借款合同

甲方（出借人）：${l.lender}
乙方（借款人）：${l.borrower}

一、借款金额
乙方向甲方借款人民币（大写）${O(l.amount)}元整（￥${l.amount}元）。

二、借款期限
${l.period}。

三、借款利息
${l.rate?`双方约定借款年利率为 ${l.rate}%，利随本清。`:"本借款为无息借款。"}

四、还款方式
乙方应于借款到期日一次性向甲方归还全部借款本金及利息。

五、违约责任
乙方未按期还款的，应按逾期金额每日万分之五向甲方支付违约金。

六、争议解决
本合同履行过程中发生争议，双方应协商解决；协商不成的，可向甲方所在地人民法院提起诉讼。

七、其他
本合同一式两份，甲乙双方各执一份，自双方签字（盖章）之日起生效。

甲方（签字/盖章）：                    乙方（签字/盖章）：

日期：${e}`;case"labor":return`劳动合同

甲方（用人单位）：${l.employer}
乙方（劳动者）：${l.worker}

根据《中华人民共和国劳动合同法》及相关法律法规，甲乙双方在平等自愿、协商一致的基础上，签订本合同。

一、合同期限
${l.period}。

二、工作岗位与内容
乙方同意根据甲方工作需要，担任${l.position}岗位工作，应按时、保质完成工作任务。

三、劳动报酬
甲方每月以货币形式向乙方支付工资，月工资标准为人民币${l.salary}元，于每月15日前发放。

四、工作时间与休息休假
甲方安排乙方执行标准工时制度，乙方依法享有法定节假日、年休假等休息权利。

五、社会保险
甲方依法为乙方缴纳基本养老、医疗、失业、工伤、生育保险及住房公积金。

六、合同的解除与终止
双方解除、终止劳动合同应依照《劳动合同法》的规定执行，符合条件的甲方应支付经济补偿。

七、争议解决
因履行本合同发生争议，可向劳动争议仲裁委员会申请仲裁。

甲方（盖章）：                          乙方（签字）：

日期：${e}`;case"rent":return`租赁合同

甲方（出租方）：${l.lessor}
乙方（承租方）：${l.lessee}

根据《中华人民共和国民法典》及相关规定，双方就租赁事宜达成如下协议：

一、租赁物
甲方将位于${l.target}的房屋/设施出租给乙方使用。

二、租赁期限
${l.period}。

三、租金及支付方式
月租金为人民币${l.rent}元，乙方按【月/季】提前支付，首期租金于交付租赁物之日支付。

四、押金
乙方于签约时向甲方支付相当于一个月租金的押金，租赁期满且乙方无违约的，甲方全额无息退还。

五、双方权利义务
甲方保证租赁物权属清晰、可正常使用；乙方应合理使用租赁物，不得擅自转租或改变用途。

六、违约责任
任何一方违约，应向守约方支付相当于一个月租金的违约金；造成损失的，还应承担赔偿责任。

七、争议解决
协商不成的，可向租赁物所在地人民法院起诉。

甲方（签字/盖章）：                    乙方（签字/盖章）：

日期：${e}`;default:return`民事起诉状

原告：${l.plaintiff}

被告：${l.defendant}

诉讼请求：
${l.claim}

事实与理由：
${l.reason}

综上所述，被告的行为已严重损害原告的合法权益。为维护自身合法权益，原告依据《中华人民共和国民事诉讼法》的相关规定，特向贵院提起诉讼，恳请依法判如所请。

此致
XXXX人民法院

具状人（签名）：

${e}`}},O=l=>{const e=Number(l);if(!e)return"零";const r=["零","壹","贰","叁","肆","伍","陆","柒","捌","玖"],x=["","拾","佰","仟","万","拾","佰","仟","亿"],h=Math.floor(e),y=String(h);let C="";for(let v=0;v<y.length;v++){const c=Number(y[v]),I=x[y.length-1-v];C+=c===0?r[0]:r[c]+I}return C.replace(/零+/g,"零").replace(/零$/,"")},U=()=>{P.success("文书已生成，正式环境将在此处下载 Word/PDF 文件")},j=()=>{clearInterval(w),_.value=null,$.value="",f.value=0,u.value=0};return(l,e)=>{const r=i("el-step"),x=i("el-steps"),h=i("el-icon"),y=i("el-input"),C=i("el-form-item"),v=i("el-form"),c=i("el-button"),I=i("el-progress"),H=i("el-tag");return n(),d("div",te,[e[11]||(e[11]=t("section",{class:"page-hero"},[t("div",{class:"container"},[t("h1",{class:"page-hero__title"},"智能文书生成"),t("p",{class:"page-hero__desc"},"三步生成规范法律文书 · 涵盖合同、诉讼等常用场景")])],-1)),t("section",oe,[o(x,{active:u.value,"align-center":"",class:"doc-steps"},{default:a(()=>[o(r,{title:"选择类型",description:"选择需要的文书"}),o(r,{title:"填写信息",description:"补充关键条款信息"}),o(r,{title:"生成预览",description:"AI 一键生成文书"})]),_:1},8,["active"]),u.value===0?(n(),d("div",ae,[(n(),d(T,null,z(S,s=>t("div",{key:s.key,class:"type-card",onClick:M=>X(s)},[t("div",ne,[o(h,{size:26},{default:a(()=>[(n(),G(q(s.icon)))]),_:2},1024)]),t("h3",re,b(s.name),1),t("p",ce,b(s.desc),1),e[0]||(e[0]=t("span",{class:"type-card__action"},"选择并填写 →",-1))],8,se)),64))])):u.value===1?(n(),d("div",ie,[t("h2",de,[o(h,null,{default:a(()=>[o(g(K))]),_:1}),p(" "+b(_.value.name)+" · 信息填写 ",1)]),o(v,{"label-position":"top",class:"doc-form"},{default:a(()=>[(n(!0),d(T,null,z(N.value,s=>(n(),G(C,{key:s.prop,label:s.label},{default:a(()=>[o(y,{modelValue:m[s.prop],"onUpdate:modelValue":M=>m[s.prop]=M,placeholder:s.placeholder,clearable:""},null,8,["modelValue","onUpdate:modelValue","placeholder"])]),_:2},1032,["label"]))),128))]),_:1}),t("div",pe,[o(c,{icon:g(A),onClick:V},{default:a(()=>[...e[1]||(e[1]=[p("上一步",-1)])]),_:1},8,["icon"]),o(c,{type:"primary",class:"gold-btn",onClick:E},{default:a(()=>[...e[2]||(e[2]=[p(" 开始生成文书 ",-1)])]),_:1})])])):(n(),d("div",ue,[D.value?(n(),d("div",_e,[o(h,{size:40,color:"#c9a96e",class:"generating__icon"},{default:a(()=>[o(g(B))]),_:1}),t("p",me,"AI 正在为您生成《"+b(_.value.name)+"》...",1),o(I,{percentage:f.value,"stroke-width":10,color:"#c9a96e",class:"generating__bar"},null,8,["percentage"]),e[3]||(e[3]=t("p",{class:"generating__tips"},"正在匹配标准条款库、校验法律要素",-1))])):(n(),d(T,{key:1},[t("div",fe,[t("div",null,[t("h2",ve,"《"+b(_.value.name)+"》已生成",1),e[4]||(e[4]=t("p",{class:"result-subtitle"},"请仔细核对文书内容，确认无误后可下载使用",-1))]),o(H,{type:"success",size:"large",effect:"light"},{default:a(()=>[...e[5]||(e[5]=[p("生成成功",-1)])]),_:1})]),t("div",ge,b($.value),1),t("div",be,[o(c,{icon:g(B),onClick:F},{default:a(()=>[...e[6]||(e[6]=[p("重新生成",-1)])]),_:1},8,["icon"]),o(c,{icon:g(A),onClick:V},{default:a(()=>[...e[7]||(e[7]=[p("修改信息",-1)])]),_:1},8,["icon"]),o(c,{icon:g(Q),type:"primary",class:"gold-btn",onClick:U},{default:a(()=>[...e[8]||(e[8]=[p(" 下载文书 ",-1)])]),_:1},8,["icon"]),o(c,{text:"",onClick:j},{default:a(()=>[...e[9]||(e[9]=[p("再写一份",-1)])]),_:1})]),e[10]||(e[10]=t("p",{class:"result-tip"}," 提示：AI 生成文书仅供参考，正式签署前建议请执业律师审核，以规避法律风险。 ",-1))],64))]))])])}}},$e=J(he,[["__scopeId","data-v-568f0d07"]]);export{$e as default};
