# PureSushi Channel Commands

---
## CustomCommands

### addcom COMMAND TEXT
```
addcom newcom I'm a new command
```
### delcom COMMAND
```
delcom newcom
```
---
## ShoutoutCommands

### shoutout (@)USER
```
shoutout PureSushi

shoutout @PureSushi
```
**Remarks**

Mod Only. Promotes the given user's channel.

---
## QuoteCommands

### quote (ID)
```
quote

quote 123
```
### quote add TEXT
```
quote add Hi, I'm a PureSushi quote
```
**Remarks**

Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.

### quote del ID
```
quote del 123

quote del last
```
### quote change ID TEXT
```
quote change 12 Hi, I'm a better PureSushi quote
```
**Remarks**

Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.

---
## ScoreCommands

### purecount
### pureboard
### curseboard
### clearboard
**Remarks**

Mod Only. Clears leaderboard.

---
## TimeCommands

### uptime
---
## VoteBanCommands

### voteban (@)USER
```
voteban BabotzInc

voteban @BabotzInc
```
**Remarks**

This is a joke command.

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
## PollCommands

### poll NUM_MINUTES (NUM_OPTIONS)
```
poll 2

poll 4 3
```
**Remarks**

A Yes/No poll is started when NUM_OPTIONS is not provided. NUM_OPTIONS may be 2-10 and will start a poll with A, B, C, etc.

### poll end
### vote LETTER
```
vote y
```
---
## WhoCommands

### who (@USER) (ID)
```
who

who 14

who @BabotzInc

who @BabotzInc 14
```
**Remarks**

When no username is given, this command defaults to your own quotes.

### who add @USER TEXT
```
who add @BabotzInc Hello I'm a Babotz quote
```
**Remarks**

@ing the user is required. Type @ and use Twitch's username picker/autocomplete to ensure the correct username is given.

### who del @USER ID
```
who del @BabotzInc 12
```
**Remarks**

@ing the user is required. Type @ and use Twitch's username picker/autocomplete to ensure the correct username is given.


---
## Other Commands

```
deathcount
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
lore
```
```
puresushi
```
```
thanks
```
```
truth
```
```
what
```
```
wrench
```
```
lewdcount
```
```
discord
```
```
bonsai
```
```
chateau
```
```
compilation
```
```
youtube
```
```
twitter
```
```
multi
```
```
movienight
```
```
list
```
```
welcome [ARG]
```
```
help
```
```
commands
```
```
sushiwall
```
```
fbi
```
```
drive
```

