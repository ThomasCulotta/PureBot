# PureSushi Channel Commands

---
## CustomCommands

### addcom COMMAND TEXT
```
addcom newcom I'm a new command
```
**Remarks**

Mod Only.

### delcom COMMAND
```
delcom newcom
```
**Remarks**

Mod Only.

---
## DiceCommands

### roll NUMdNUM
```
roll 1d20

roll 7d100
```
**Remarks**

Between 1 and 10 dice may be rolled. Dice options are d2 to d100.

---
## FindFoodCommands

### findfood TEXT
```
findfood burger

findfood chicken alfredo
```
---
## FindGameCommands

### findgame TEXT
```
findgame Halo

findgame Silent Hill
```
---
## FindSongCommands

### findsong TEXT
```
findsong Piano Man

findsong Killer Queen
```
---
## PollCommands

### poll NUM_MINUTES (NUM_OPTIONS)
```
poll 2

poll 4 3
```
**Remarks**

Mod Only. A Yes/No poll is started when NUM_OPTIONS is not provided. NUM_OPTIONS may be 2-10 and will start a poll with A, B, C, etc.

### vote LETTER
```
vote y
```
### poll end
**Remarks**

Mod Only.

---
## QuoteCommands

### quote (ID/TEXT)
```
quote

quote 123

quote hello
```
**Remarks**

When "quote TEXT" is used, a random quote with the given text in it is returned.

### quote add TEXT
```
quote add Hi, I'm a PureSushi quote
```
**Remarks**

Mod Only. Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.

### quote del ID
```
quote del 123

quote del last
```
**Remarks**

Mod Only.

### quote change ID TEXT
```
quote change 12 Hi, I'm a better PureSushi quote
```
**Remarks**

Mod Only. Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.

---
## ScoreCommands

### purecount
### pureboard
### curseboard
### clearboard
**Remarks**

Mod Only. Clears leaderboard.

### stealscore USER
```
stealscore BabotzInc
```
**Remarks**

Requires spending sushi rolls. Only needed when you don't provide a name in the reward message.

### swapscore USER
```
swapscore BabotzInc
```
**Remarks**

Requires spending sushi rolls. Only needed when you don't provide a name in the reward message.

---
## ShoutoutCommands

### shoutout USER
```
shoutout PureSushi

shoutout @PureSushi
```
**Remarks**

Mod Only. Promotes the given user's channel.

---
## TimeCommands

### uptime
---
## VoteBanCommands

### voteban USER
```
voteban BabotzInc

voteban @BabotzInc
```
**Remarks**

This is a joke command.

---
## WhoCommands

### who (USER) (ID)
```
who

who 14

who @BabotzInc

who BabotzInc 14
```
**Remarks**

When no username is given, this command defaults to your own quotes.

### who add USER TEXT
```
who add @BabotzInc Hello I'm a Babotz quote
```
**Remarks**

Mod Only. @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.

### who del USER ID
```
who del @BabotzInc 12
```
**Remarks**

Mod Only. @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.


---
## Other Commands

```
bonsai
```
```
chateau
```
```
commands
```
```
compilation
```
```
deathcount
```
```
discord
```
```
drive
```
```
fbi
```
```
help
```
```
hydrate
```
```
kick
```
```
leonhelp
```
```
lewdcount
```
```
list
```
```
lore
```
```
movienight
```
```
multi
```
```
puresushi
```
```
sushiwall
```
```
thanks
```
```
truth
```
```
twitter
```
```
what
```
```
wrench
```
```
youtube
```
```
zach
```

