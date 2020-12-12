#include <stdio.h>
#include <stdlib.h>
#include "sqlite3.h"

char* file_get_contents(char*);
sqlite3* initDB();
int adicionaPapel(sqlite3* db, char* codPapel[], float precoUnitario, int qtd)

int main(int argc, char *argv[]){
	sqlite3 *db = NULL;
	db = initDB();
	if(!db){
	    printf("Erro ao abrir o banco");
	    exit(1);
	}
	sqlite3_close(db);
        return 0;
}

/**
 * Inicializa o banco da Aplicacao (SQLite)
 *
 * return sqlite3*
 */

sqlite3* initDB(){
    const char dbname[]="invest.db";
    sqlite3 *db = NULL;
    FILE *fp = NULL;
    char *err = NULL;
    int rc= 0, flInit = 0;

    /** 
     *  Como sqlite3_open() cria um banco novo caso nao exista
     *  É necessario saber se ele foi criado anteriormente
     *  Ou esta sendo criado agora
     *  Caso nao exista tem que inicializar as tabelas
    */
    fp = fopen(dbname, "rb");
    if (!fp) {flInit =1;}
    else {fclose(fp);}

    rc = sqlite3_open(dbname, &db);
    if (rc!=SQLITE_OK){
	fprintf(stderr, "Não foi possivel abrir o banco: %s\n", sqlite3_errmsg(db));
	sqlite3_close(db);
	return NULL;
    }

    if(flInit){
	char *SQL=NULL;
	SQL = file_get_contents("install/initdb.sql");	
	rc = sqlite3_exec(db, SQL, NULL, NULL, &err);
	free(SQL);
	if ( rc != SQLITE_OK ) {
	    fprintf (stderr, "Erro ao executar o SQL: %s\n", err);
	    sqlite3_free(err);
	}
    }
    return db;


}

char* file_get_contents(char *filename){
	long len;
	FILE *fp;
	char *buffer = NULL;

	if((fp = fopen(filename,"r"))==NULL){
	    printf("Erro ao abrir arquivo");
	    exit(1);
	 }
	fseek(fp, 0, SEEK_END);
	len = ftell(fp);
	fseek(fp, 0, SEEK_SET);
	buffer = malloc(len+1);
	if (buffer){
	    fread(buffer, 1, len, fp);
	    buffer[len]='\0';
	}
	fclose(fp);
	return buffer;	
}

int adicionaPapel(sqlite3* db, char* codPapel[], float precoUnitario, int qtd){
	const char SQL[]="INSERT INTO TABLE TB_APLICACAO VALUES (NULL, ?, ?, ?, ?, ?, ?";

}

