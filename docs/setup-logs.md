# Comment exporter vos logs serveur

Le script `parse-logs.py` attend un fichier au format Nginx `combined` (qui est aussi le format `combined` d'Apache). Voici comment récupérer vos logs selon votre hébergement.

---

## Nginx (VPS, dédié, OVH, Hetzner, etc.)

Les logs sont par défaut dans `/var/log/nginx/access.log`.

```bash
# Connectez-vous en SSH
ssh user@votre-serveur.com

# Téléchargez le log
scp user@votre-serveur.com:/var/log/nginx/access.log ./access.log
```

Si la rotation est active (logrotate), récupérez aussi les fichiers archivés :

```bash
# Liste des archives
ls /var/log/nginx/access.log*

# Téléchargez tout
scp user@votre-serveur.com:/var/log/nginx/access.log* ./logs/

# Décompressez et concaténez (si .gz)
gunzip ./logs/*.gz
cat ./logs/access.log* > ./access-combined.log
```

---

## Apache (cPanel mutualisé : o2switch, OVH, Hostinger, PlanetHoster)

Le format Apache `combined` est identique au Nginx `combined`. Le parser fonctionne directement.

### Sur cPanel (o2switch, PlanetHoster)

1. Connectez-vous à cPanel.
2. Section **Métriques** → **Accès brut** (ou "Raw Access Logs").
3. Cochez "Archive les journaux".
4. Téléchargez le `.gz` correspondant à votre domaine.
5. Décompressez :

```bash
gunzip votredomaine.fr.gz
mv votredomaine.fr access.log
```

### Sur OVH mutualisé

1. Espace client OVH → **Hébergement** → votre hébergement.
2. Onglet **Logs**.
3. Téléchargez le fichier de la période voulue.

### Sur Hostinger

1. hPanel → **Performance** → **Logs d'accès**.
2. Bouton "Télécharger".

---

## WordPress (sans accès serveur direct)

Si vous êtes sur WordPress sans accès aux logs, deux options :

### Option 1 : Plugin de logging

Installez **Crawl Detect** ou **Bot Tracker** (cherche dans le repo plugin WP). Le plugin écrit chaque hit bot dans la base WP. Exportez en CSV via le plugin, puis convertissez au format Nginx combined avec un script — non couvert ici, c'est sale.

**Recommandation : passez plutôt par l'hébergeur** (voir Apache cPanel ci-dessus). Tous les WordPress hébergés en mutualisé ont des logs Apache accessibles.

### Option 2 : Cloudflare devant WordPress

Si vous avez Cloudflare devant votre WordPress (ce qui est fréquent), utilisez les logs Cloudflare (section suivante). Ils contiennent les hits bots AVANT que WordPress ne les voit.

---

## Cloudflare (Workers, Pages, ou proxy devant un site)

Cloudflare propose deux mécanismes selon votre plan :

### Plan gratuit / Pro : pas de logs détaillés

Le plan gratuit n'expose pas de logs détaillés par hit. Vous avez juste des stats agrégées dans le dashboard. Le parser ne s'applique pas.

Workaround : activer un Worker qui log chaque requête bot dans une KV ou un Workers Analytics Engine. Hors scope de ce toolkit.

### Plan Business / Enterprise : Logpush

Logpush envoie tous les logs vers S3, R2, GCS, Sumo Logic, etc. Le format est JSON, pas Nginx combined.

Pour convertir un Logpush JSON en format Nginx, utilisez `jq` :

```bash
jq -r '.[] | "\(.ClientIP) - - [\(.EdgeStartTimestamp | strftime("%d/%b/%Y:%H:%M:%S +0000"))] \"\(.ClientRequestMethod) \(.ClientRequestURI) HTTP/\(.ClientRequestHTTPProtocol)\" \(.EdgeResponseStatus) \(.EdgeResponseBytes) \"\(.ClientRequestReferer // "-")\" \"\(.ClientRequestUserAgent)\""' \
  cf-logs.json > access.log
```

Puis appliquez `parse-logs.py` normalement.

---

## Vérifier que vos logs contiennent bien les User-Agents

Si le rapport renvoie "Aucun bot détecté", vérifiez d'abord que vos logs incluent bien la colonne User-Agent :

```bash
# Doit afficher des User-Agents entre guillemets en fin de ligne
head -3 access.log
```

Si la dernière colonne `"..."` est vide ou manquante, votre format n'est pas `combined`. Ajustez la config du serveur :

### Nginx — `/etc/nginx/nginx.conf`

```nginx
log_format combined '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent"';

access_log /var/log/nginx/access.log combined;
```

### Apache — `httpd.conf` ou `.htaccess`

```apache
LogFormat "%h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"" combined
CustomLog logs/access_log combined
```

Redémarrez le serveur après modification.

---

## Période recommandée pour une mesure exploitable

- **Minimum** : 7 jours, sinon trop de variance.
- **Idéal** : 30 jours, pour voir les cycles hebdo des bots.
- **Trimestre** : pour comparer mois à mois.

Avec 30 jours de logs d'un site qui reçoit 5k visiteurs/mois, comptez entre 5 et 50 Mo de logs bruts. C'est gérable en local.
