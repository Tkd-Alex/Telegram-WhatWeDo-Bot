# WhatWeDo?

### CONTESTO
Il Bot opera all’interno di un gruppo Telegram e analizza tutti i messaggi scambiati
all’interno dello stesso. Per ogni messaggio effettua un parsing delle parole presenti
all’interno del testo e tramite la libreria TreeTagger classifica ogni parola all’interno della
grammatica italiana. Giocano un ruolo molto importante i verbi e le preposizioni in
quanto permettono di capire se la frase contiene l’intenzione di voler fare qualcosa,
oppure vi è una nuova proposta ad un sondaggio già aperto.
Ad esempio, nella frase: “Ciao ragazzi, come va? Volete fare qualcosa domani sera? Io
pensavo di andare al cinema per passare un po' di tempo insieme.”, vi sono le parole
chiave per creare un nuovo sondaggio e popolarlo già con una prima proposta.
Innanzitutto, il testo viene suddiviso in tre frasi:

1. Ciao ragazzi, come va?
2. Volete fare qualcosa domani sera?
3. Io pensavo di andare al cinema per passare un po' di tempo insieme.

Nella prima frase non vi è alcuna parola di particolare importanza, dunque viene scartata.
Nella seconda, invece, grazie al verbo “fare” coniugato all’infinito, seguito da “domani
sera” è facile intuire che si sta proponendo al gruppo di voler intraprendere un’azione
nella serata di domani, di conseguenza il Bot aprirà il sondaggio avente come titolo il
messaggio originariamente inviato. Analizzando la terza frase inoltre, è possibile capire
che l’utente sta persino proponendo un luogo in cui andare, in quanto, vi è presente il
verbo “andare” coniugato all’infinito, seguito dalla preposizione articolata “al” seguita
a sua volta da un nome, ovvero il cinema. Pertanto, il Bot aggiungerà automaticamente al
sondaggio precedentemente aperto “Andare al cinema” come un’eventuale scelta per la
serata aspettando che a sua volta gli altri componenti del gruppo esprimano le proprie
opinioni.

### OBIETTIVO
Quando un gruppo è formato da tanti partecipanti non è sempre facile organizzarsi e
trovare un punto d’incontro che vada bene a tutti. Inoltre, le varie proposte potrebbero
essere sommerse da altri messaggi magari “off-topic”. Per questo motivo il progetto si
offre come un ottimo strumento di supporto raccogliendo sotto di esso tutte le proposte
date prima che venga chiuso. Ogni proposta sarà accompagnata dal numero di voti
ottenuti, i quali si aggiorneranno automaticamente ogni qualvolta un utente esprime la
propria volontà. Il sondaggio potrà poi essere chiuso manualmente dall’utente utilizzando
un comando del Bot oppure attendere che il Bot lo chiuda in automatico. Ogni indagine
ha un “marcatore temporale” che indica giorno e orario per cui è stata aperta. Ad esempio,
utilizzando la frase presente nel sotto capitolo 1.1, il Bot chiuderà automaticamente il
sondaggio il giorno successivo alla sua apertura alle ore 20:00, in quanto, il testo
conteneva le parole “domani sera”. Ogni qualvolta un sondaggio si conclude verrà
inviato nel gruppo un messaggio contenente la proposta vincitrice.
