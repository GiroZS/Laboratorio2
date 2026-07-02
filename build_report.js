const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
        ShadingType, TableOfContents, PageBreak } = require("docx");

const FONT = "Arial";
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function h1(t){return new Paragraph({heading:HeadingLevel.HEADING_1,children:[new TextRun(t)]});}
function h2(t){return new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(t)]});}
function p(t){return new Paragraph({spacing:{after:120},children:[new TextRun(t)]});}
function code(t){return new Paragraph({spacing:{after:60},shading:{fill:"F2F2F2",type:ShadingType.CLEAR},
  children:[new TextRun({text:t,font:"Courier New",size:18})]});}
function bullet(t){return new Paragraph({numbering:{reference:"b",level:0},children:[new TextRun(t)]});}

function cell(t, head=false, w=3120){
  return new TableCell({borders, width:{size:w,type:WidthType.DXA},
    shading: head?{fill:"D5E8F0",type:ShadingType.CLEAR}:undefined,
    margins:{top:80,bottom:80,left:120,right:120},
    children:[new Paragraph({children:[new TextRun({text:t,bold:head})]})]});
}
function row(cells,head=false,widths){return new TableRow({children:cells.map((c,i)=>cell(c,head,widths[i]))});}

const msgTable = new Table({
  width:{size:9360,type:WidthType.DXA}, columnWidths:[1800,7560],
  rows:[
    row(["Mensagem","Significado"],true,[1800,7560]),
    row(["HELLO","Anúncio de presença na subida do nó."],false,[1800,7560]),
    row(["REQUEST","Pedido de entrada na seção crítica (Ricart-Agrawala), carrega o timestamp do pedido."],false,[1800,7560]),
    row(["REPLY","Permissão para o remetente entrar na seção crítica."],false,[1800,7560]),
    row(["ELECTION","Início/propagação de eleição (Bully), enviado a nós de id maior."],false,[1800,7560]),
    row(["ANSWER","Resposta de um nó vivo de id maior, suprimindo a candidatura do remetente."],false,[1800,7560]),
    row(["COORDINATOR","Anúncio do novo líder a todos os nós."],false,[1800,7560]),
  ]
});

const doc = new Document({
  styles:{
    default:{document:{run:{font:FONT,size:22}}},
    paragraphStyles:[
      {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,
        run:{size:30,bold:true,font:FONT,color:"1F4E79"},
        paragraph:{spacing:{before:240,after:160},outlineLevel:0}},
      {id:"Heading2",name:"Heading 2",basedOn:"Normal",next:"Normal",quickFormat:true,
        run:{size:25,bold:true,font:FONT,color:"2E75B6"},
        paragraph:{spacing:{before:180,after:120},outlineLevel:1}},
    ]
  },
  numbering:{config:[{reference:"b",levels:[{level:0,format:LevelFormat.BULLET,text:"•",
    alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:720,hanging:360}}}}]}]},
  sections:[{
    properties:{page:{size:{width:12240,height:15840},margin:{top:1440,right:1440,bottom:1440,left:1440}}},
    children:[
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:80},
        children:[new TextRun({text:"MC714 — Sistemas Distribuídos",bold:true,size:36,color:"1F4E79"})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:80},
        children:[new TextRun({text:"2º Trabalho — Implementação de Algoritmos Distribuídos",bold:true,size:26})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:40},
        children:[new TextRun({text:"Instituto de Computação — UNICAMP",size:22})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:240},
        children:[new TextRun({text:"Prof. Luiz Fernando Bittencourt",size:22})]}),

      new Paragraph({spacing:{after:60},children:[new TextRun({text:"Participantes:",bold:true})]}),
      p("Nome: ____________________________    RA: __________"),
      p("Nome: ____________________________    RA: __________"),
      new Paragraph({spacing:{after:120},children:[
        new TextRun({text:"Repositório: ",bold:true}),
        new TextRun("https://github.com/<usuario>/mc714-trabalho2")]}),
      new Paragraph({spacing:{after:240},children:[
        new TextRun({text:"Vídeo: ",bold:true}),
        new TextRun("https://<link-do-video>")]}),

      new Paragraph({children:[new TextRun({text:"Sumário",bold:true,size:26})]}),
      new TableOfContents("Sumário",{hyperlink:true,headingStyleRange:"1-2"}),
      new Paragraph({children:[new PageBreak()]}),

      h1("1. O Problema"),
      p("Sistemas distribuídos são compostos por processos autônomos que não compartilham memória nem um relógio físico comum e que coordenam suas ações exclusivamente por troca de mensagens sobre uma rede sujeita a atrasos. Três problemas fundamentais surgem nesse contexto: (i) ordenar eventos que ocorrem em máquinas diferentes sem um relógio global; (ii) garantir que, mesmo concorrentemente, no máximo um processo acesse um recurso compartilhado por vez (exclusão mútua); e (iii) eleger, de forma descentralizada e tolerante a falhas, um processo coordenador (líder)."),
      p("Este trabalho implementa, sobre uma única infraestrutura de comunicação por troca de mensagens (sockets TCP), os três algoritmos clássicos que resolvem esses problemas, conforme exigido pelo enunciado."),

      h1("2. Algoritmos Escolhidos"),
      h2("2.1 Relógio Lógico de Lamport"),
      p("O relógio de Lamport (Lamport, 1978) atribui a cada evento um contador inteiro que respeita a relação de causalidade \"happened-before\". As regras implementadas são:"),
      bullet("Antes de qualquer evento local ou envio de mensagem, o processo incrementa o seu relógio."),
      bullet("Toda mensagem leva anexado o valor atual do relógio (timestamp)."),
      bullet("Ao receber uma mensagem com timestamp t, o processo faz clock = max(clock_local, t) + 1."),
      p("Isso garante que, se um evento a causa um evento b, então C(a) < C(b). O relógio é usado também como critério de desempate na exclusão mútua."),

      h2("2.2 Exclusão Mútua — Ricart-Agrawala"),
      p("O algoritmo de Ricart-Agrawala (1981) é um algoritmo distribuído baseado em permissões que dispensa um coordenador central. Para entrar na seção crítica, um processo envia REQUEST com o timestamp de Lamport a todos os demais e só entra após receber REPLY de todos."),
      p("Ao receber um REQUEST, um processo responde imediatamente com REPLY, exceto se ele próprio deseja a seção crítica e tem prioridade — ou seja, se o seu par (timestamp, id) for menor que o par do solicitante. Nesse caso o REPLY é adiado e enviado apenas quando o processo sai da seção crítica. O par (timestamp, id) garante uma ordem total, evitando empates e starvation."),

      h2("2.3 Eleição de Líder — Bully"),
      p("O algoritmo Bully (Garcia-Molina, 1982) elege como líder o processo de maior identificador. Quando um processo inicia uma eleição, envia ELECTION a todos os processos de id maior. Se algum responde com ANSWER, ele desiste e aguarda o anúncio do líder. Se ninguém de id maior responde dentro de um timeout, ele se declara líder e envia COORDINATOR a todos. Cada processo que recebe ELECTION responde ANSWER e inicia a sua própria eleição, propagando o processo até que o de maior id vença."),

      new Paragraph({children:[new PageBreak()]}),
      h1("3. Detalhes da Implementação"),
      h2("3.1 Linguagem e bibliotecas"),
      p("A solução foi escrita em Python 3.11 usando apenas a biblioteca padrão (módulos socket, threading e json). Não há dependências externas, o que mantém a imagem Docker enxuta e a compilação trivial."),
      h2("3.2 Sistema de comunicação"),
      p("A comunicação é troca de mensagens real pela rede, via sockets TCP. Cada nó executa um servidor TCP (classe MessageServer) que aceita conexões e entrega mensagens a um callback. As mensagens são objetos JSON delimitados por nova linha (newline-delimited JSON). O envio (send_message) abre uma conexão por mensagem, com reconexão automática enquanto o destino ainda não está no ar — útil na subida simultânea dos contêineres. Importante: não há simulação por arquivo; toda coordenação ocorre por mensagens na rede."),
      p("Cada mensagem carrega os campos type (tipo), src (id do remetente) e ts (timestamp de Lamport). Os tipos são:"),
      msgTable,
      new Paragraph({spacing:{before:120}}),
      h2("3.3 Arquitetura de componentes"),
      bullet("lamport.py — implementação isolada e thread-safe do relógio de Lamport."),
      bullet("transport.py — camada de transporte (servidor TCP + função de envio)."),
      bullet("node.py — classe Node que integra os três algoritmos e despacha mensagens por tipo."),
      bullet("main.py — ponto de entrada de cada nó; lê a topologia de PEERS e o papel de demonstração de ROLE."),
      bullet("config.py — topologia padrão para execução local."),
      bullet("test_local.py — sobe 3 nós em threads e exercita os três algoritmos automaticamente."),

      h2("3.4 Ambiente de execução"),
      p("O sistema roda de três formas equivalentes: (a) localmente com test_local.py para validação rápida; (b) em contêineres Docker orquestrados por docker-compose, com cada nó em um contêiner próprio numa rede bridge; (c) em VMs distintas na GCloud, bastando definir a variável PEERS com os IPs e portas e liberar as portas no firewall. O mesmo código serve aos três cenários, pois a topologia é externa ao código."),

      new Paragraph({children:[new PageBreak()]}),
      h1("4. Testes e Resultados"),
      p("A execução de teste com três nós produziu os seguintes comportamentos observados nos logs (cada linha mostra o relógio de Lamport do nó no momento do evento)."),
      h2("4.1 Relógio de Lamport"),
      p("Os contadores avançam monotonicamente e aplicam a regra max+1 a cada recepção, preservando a ordem causal entre HELLO, REQUEST/REPLY e mensagens de eleição."),
      h2("4.2 Exclusão Mútua"),
      p("Com os nós 1 e 3 disputando a seção crítica quase simultaneamente, o nó com menor (timestamp, id) entrou primeiro; o outro teve o seu REPLY adiado e só entrou após o primeiro liberar a seção. Em nenhum instante dois nós estiveram na seção crítica ao mesmo tempo — a propriedade de exclusão mútua foi mantida."),
      code("[no 1] PEDE seção crítica (ts=9)"),
      code("[no 1] >>> ENTROU na seção crítica <<<"),
      code("[no 1] ADIOU REPLY para 3 (tenho prioridade)"),
      code("[no 1] <<< SAIU da seção crítica >>>"),
      code("[no 3] >>> ENTROU na seção crítica <<<"),
      h2("4.3 Eleição de Líder"),
      p("Quando o nó 1 (menor id) iniciou a eleição, os nós 2 e 3 responderam ANSWER e iniciaram suas próprias eleições; o nó 3 (maior id) não obteve resposta de nenhum superior e se declarou líder, anunciando-se via COORDINATOR. Ao final, todos os nós reconheceram o líder = 3."),
      code("[no 1] INICIA ELEIÇÃO. Nós com id maior: [2, 3]"),
      code("[no 3] *** SOU O NOVO LÍDER (id=3) ***"),
      code("no 1 reconhece lider = 3 / no 2 reconhece lider = 3 / no 3 reconhece lider = 3"),

      h1("5. Fontes Utilizadas e Alterações"),
      p("A implementação foi escrita do zero para este trabalho, baseada na descrição dos algoritmos nas referências abaixo. Não foi copiado código de terceiros; apenas a lógica dos algoritmos seguiu o que está descrito na literatura clássica."),
      bullet("Lamport, L. (1978). Time, Clocks, and the Ordering of Events in a Distributed System. CACM."),
      bullet("Ricart, G.; Agrawala, A. (1981). An Optimal Algorithm for Mutual Exclusion in Computer Networks. CACM."),
      bullet("Garcia-Molina, H. (1982). Elections in a Distributed Computing System. IEEE Trans. on Computers."),
      bullet("Tanenbaum, A.; van Steen, M. Distributed Systems: Principles and Paradigms."),
      p("Caso algum trecho de código de terceiros venha a ser incorporado, a fonte e as alterações realizadas devem ser declaradas aqui, conforme exige o enunciado."),

      h1("6. Comentários sobre a Experiência"),
      p("Implementar os três algoritmos sobre uma mesma camada de mensagens evidenciou como o relógio de Lamport é a base que torna a exclusão mútua de Ricart-Agrawala justa e livre de starvation, por fornecer uma ordem total entre pedidos concorrentes. O algoritmo Bully, por sua vez, mostrou-se simples de implementar e eficaz, ao custo de muitas mensagens quando o nó de menor id inicia a eleição. O uso de Docker facilitou reproduzir um ambiente verdadeiramente distribuído na própria máquina, sem recorrer a simulação por arquivos."),
    ]
  }]
});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("Relatorio.docx",b);console.log("ok");});
